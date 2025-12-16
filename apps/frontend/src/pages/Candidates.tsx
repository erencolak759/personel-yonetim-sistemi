import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import type { Candidate, Position } from '../types'
import { useState } from 'react'

interface CandidateForm {
  ad: string
  soyad: string
  telefon: string
  email: string
  pozisyon_id: string
  basvuru_tarihi: string
  gorusme_tarihi: string
  durum: string
  aciklama: string
}

export default function Candidates() {
  const queryClient = useQueryClient()

  const [form, setForm] = useState<CandidateForm>({
    ad: '',
    soyad: '',
    telefon: '',
    email: '',
    pozisyon_id: '',
    basvuru_tarihi: new Date().toISOString().slice(0, 10),
    gorusme_tarihi: '',
    durum: 'Basvuru Alindi',
    aciklama: '',
  })

  const { data: candidates, isLoading } = useQuery<Candidate[]>({
    queryKey: ['candidates'],
    queryFn: async () => {
      const res = await api.get('/candidates')
      return res.data
    },
  })

  const { data: positions } = useQuery<Position[]>({
    queryKey: ['positions'],
    queryFn: async () => {
      const res = await api.get('/employees/form-data')
      return res.data.pozisyonlar
    },
  })

  const createMutation = useMutation({
    mutationFn: async (payload: CandidateForm) => {
      await api.post('/candidates', {
        ...payload,
        pozisyon_id: Number(payload.pozisyon_id),
        gorusme_tarihi: payload.gorusme_tarihi || null,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      setForm((prev) => ({
        ...prev,
        ad: '',
        soyad: '',
        telefon: '',
        email: '',
        pozisyon_id: '',
        gorusme_tarihi: '',
        durum: 'Basvuru Alindi',
        aciklama: '',
      }))
    },
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.ad || !form.soyad || !form.pozisyon_id || !form.basvuru_tarihi) return
    createMutation.mutate(form)
  }

  const toplamAday = candidates?.length || 0
  const durumGruplari = candidates?.reduce<Record<string, number>>((acc, c) => {
    acc[c.durum] = (acc[c.durum] || 0) + 1
    return acc
  }, {}) || {}

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Adaylar</h1>
        <p className="text-slate-500 mt-1">İşe alım sürecindeki adayları takip edin.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-2">Aday Özeti</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <div className="p-4 rounded-xl bg-primary-50 border border-primary-100">
              <p className="text-xs font-medium text-primary-700">Toplam Aday</p>
              <p className="text-2xl font-bold text-primary-900 mt-1">{toplamAday}</p>
            </div>
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-100">
              <p className="text-xs font-medium text-emerald-700">Aktif Süreç</p>
              <p className="text-sm text-emerald-900 mt-1">
                {(durumGruplari['Basvuru Alindi'] || 0) + (durumGruplari['Mulakat'] || 0) + (durumGruplari['Teklif'] || 0)} aday
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-xs font-medium text-slate-700">Duruma Göre Dağılım</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {Object.entries(durumGruplari).map(([durum, sayi]) => (
                  <span key={durum} className="px-2 py-0.5 rounded-full bg-white text-slate-700 text-xs border border-slate-200">
                    {durum}: {sayi}
                  </span>
                ))}
                {Object.keys(durumGruplari).length === 0 && (
                  <span className="text-xs text-slate-500">Henüz aday yok</span>
                )}
              </div>
            </div>
          </div>

          <h2 className="text-lg font-semibold text-slate-900 mb-4">Aday Listesi</h2>

          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            </div>
          ) : !candidates || candidates.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-6">Henüz aday kaydı bulunmuyor.</p>
          ) : (
            <div className="space-y-3">
              {candidates.map((c) => (
                <div
                  key={c.aday_id}
                  className="border border-slate-200 rounded-xl p-4 bg-white flex flex-col sm:flex-row sm:items-center gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-900 truncate">
                      {c.ad} {c.soyad}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Başvuru: {c.basvuru_tarihi}
                      {c.gorusme_tarihi ? ` · Görüşme: ${c.gorusme_tarihi}` : ''}
                    </p>
                    <p className="text-sm text-slate-700 mt-1">{c.pozisyon_adi}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {c.telefon || '-'}
                      {c.email ? ` · ${c.email}` : ''}
                    </p>
                  </div>
                  <div className="sm:text-right">
                    <span className="inline-flex px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs">
                      {c.durum}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Yeni Aday Ekle</h2>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Ad</label>
                <input
                  type="text"
                  name="ad"
                  value={form.ad}
                  onChange={handleChange}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Soyad</label>
                <input
                  type="text"
                  name="soyad"
                  value={form.soyad}
                  onChange={handleChange}
                  className="input"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Telefon</label>
                <input
                  type="text"
                  name="telefon"
                  value={form.telefon}
                  onChange={handleChange}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">E-posta</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  className="input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Pozisyon</label>
              <select
                name="pozisyon_id"
                value={form.pozisyon_id}
                onChange={handleChange}
                className="input"
                required
              >
                <option value="">Pozisyon seçin</option>
                {positions?.map((p) => (
                  <option key={p.pozisyon_id} value={p.pozisyon_id}>
                    {p.pozisyon_adi}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Başvuru Tarihi</label>
                <input
                  type="date"
                  name="basvuru_tarihi"
                  value={form.basvuru_tarihi}
                  onChange={handleChange}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Görüşme Tarihi</label>
                <input
                  type="date"
                  name="gorusme_tarihi"
                  value={form.gorusme_tarihi}
                  onChange={handleChange}
                  className="input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Durum</label>
              <select
                name="durum"
                value={form.durum}
                onChange={handleChange}
                className="input"
              >
                <option value="Basvuru Alindi">Başvuru Alındı</option>
                <option value="Mulakat">Mülakat</option>
                <option value="Teklif">Teklif</option>
                <option value="Red">Red</option>
                <option value="Kabul">Kabul</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Notlar</label>
              <textarea
                name="aciklama"
                value={form.aciklama}
                onChange={handleChange}
                className="input min-h-[80px]"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Kaydediliyor...' : 'Aday Ekle'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}


