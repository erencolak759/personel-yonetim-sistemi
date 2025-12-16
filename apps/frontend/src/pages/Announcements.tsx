import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import type { Announcement, User } from '../types'
import { useAuth } from '../contexts/AuthContext'
import { useState } from 'react'

interface AnnouncementForm {
  baslik: string
  icerik: string
  oncelik: 'Dusuk' | 'Normal' | 'Yuksek'
  bitis_tarihi: string
}

export default function Announcements() {
  const queryClient = useQueryClient()
  const { user } = useAuth() as { user: User | null }

  const [form, setForm] = useState<AnnouncementForm>({
    baslik: '',
    icerik: '',
    oncelik: 'Normal',
    bitis_tarihi: '',
  })

  const { data: announcements, isLoading } = useQuery<Announcement[]>({
    queryKey: ['announcements'],
    queryFn: async () => {
      const res = await api.get('/announcements')
      return res.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (payload: AnnouncementForm) => {
      await api.post('/announcements', {
        ...payload,
        olusturan_kullanici_id: user?.kullanici_id,
        bitis_tarihi: payload.bitis_tarihi || null,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['announcements'] })
      setForm({
        baslik: '',
        icerik: '',
        oncelik: 'Normal',
        bitis_tarihi: '',
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/announcements/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['announcements'] })
    },
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.baslik || !form.icerik || !user) return
    createMutation.mutate(form)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Duyurular</h1>
        <p className="text-slate-500 mt-1">Personel ile paylaşmak istediğiniz duyuruları yönetin.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6 lg:col-span-1">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Yeni Duyuru Oluştur</h2>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Başlık</label>
              <input
                type="text"
                name="baslik"
                value={form.baslik}
                onChange={handleChange}
                className="input"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">İçerik</label>
              <textarea
                name="icerik"
                value={form.icerik}
                onChange={handleChange}
                className="input min-h-[100px]"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Öncelik</label>
                <select
                  name="oncelik"
                  value={form.oncelik}
                  onChange={handleChange}
                  className="input"
                >
                  <option value="Dusuk">Düşük</option>
                  <option value="Normal">Normal</option>
                  <option value="Yuksek">Yüksek</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Bitiş Tarihi (opsiyonel)</label>
                <input
                  type="date"
                  name="bitis_tarihi"
                  value={form.bitis_tarihi}
                  onChange={handleChange}
                  className="input"
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Kaydediliyor...' : 'Duyuru Ekle'}
            </button>
          </form>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Aktif Duyurular</h2>

            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
              </div>
            ) : !announcements || announcements.length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-6">Henüz duyuru bulunmuyor.</p>
            ) : (
              <div className="space-y-4">
                {announcements.map((a) => (
                  <div
                    key={a.duyuru_id}
                    className="border border-slate-200 rounded-xl p-4 bg-white flex flex-col gap-2"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-slate-900">{a.baslik}</h3>
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              a.oncelik === 'Yuksek'
                                ? 'bg-red-100 text-red-700'
                                : a.oncelik === 'Dusuk'
                                ? 'bg-slate-100 text-slate-700'
                                : 'bg-amber-100 text-amber-700'
                            }`}
                          >
                            {a.oncelik}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 mt-1 whitespace-pre-line">{a.icerik}</p>
                      </div>
                      <button
                        onClick={() => deleteMutation.mutate(a.duyuru_id)}
                        className="text-xs text-red-600 hover:text-red-700"
                      >
                        Sil
                      </button>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
                      <span>Oluşturan: {a.olusturan}</span>
                      <span>
                        {a.yayin_tarihi}
                        {a.bitis_tarihi ? ` · Bitiş: ${a.bitis_tarihi}` : null}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


