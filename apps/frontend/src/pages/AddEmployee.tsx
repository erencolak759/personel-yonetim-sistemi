import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'
import type { Department, Position } from '../types'

export default function AddEmployee() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data } = useQuery<{ departmanlar: Department[]; pozisyonlar: Position[] }>({
    queryKey: ['employee-form-data'],
    queryFn: async () => {
      const response = await api.get('/employees/form-data')
      return response.data
    },
  })

  const mutation = useMutation({
    mutationFn: async (personelData: any) => {
      const res = await api.post('/employees', personelData)
      return res
    },
    onSuccess: async () => {
      setIsSubmitting(false)
      toast.success('Personel başarıyla eklendi')
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      navigate('/admin/employees')
    },
    onError: () => {
      toast.error('Personel eklenirken hata oluştu')
      setIsSubmitting(false)
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsSubmitting(true)
    const formData = new FormData(e.currentTarget)
    const personelData = Object.fromEntries(formData as any)
    if (!personelData.kullanici_adi || !personelData.sifre) {
      toast.error('Kullanıcı adı ve şifre zorunludur')
      setIsSubmitting(false)
      return
    }

    mutation.mutate(personelData)
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/admin/employees')}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft size={24} className="text-slate-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Yeni Personel Kaydı</h1>
          <p className="text-slate-500">Personel bilgilerini girin</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="p-6 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-emerald-600">1. Kimlik Bilgileri</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="label">TC Kimlik No</label>
              <input
                name="tc_kimlik_no"
                className="input"
                required
                maxLength={11}
                placeholder="11 haneli TC"
              />
            </div>
            <div>
              <label className="label">Ad</label>
              <input name="ad" className="input" required placeholder="Ad" />
            </div>
            <div>
              <label className="label">Soyad</label>
              <input name="soyad" className="input" required placeholder="Soyad" />
            </div>
            <div>
              <label className="label">Doğum Tarihi</label>
              <input type="date" name="dogum_tarihi" className="input" required />
            </div>
            <div>
              <label className="label">Telefon</label>
              <input name="telefon" className="input" placeholder="0555..." />
            </div>
            <div>
              <label className="label">E-posta</label>
              <input
                type="email"
                name="email"
                className="input"
                placeholder="ornek@sirket.com"
              />
            </div>
          </div>
        </div>

        <div className="card mt-6">
          <div className="p-6 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-emerald-600">
              2. Görev ve Departman Bilgileri
            </h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="label">İşe Giriş Tarihi</label>
              <input type="date" name="ise_giris_tarihi" className="input" required />
            </div>
            <div>
              <label className="label">Departman</label>
              <select name="departman_id" className="input" required>
                <option value="">Seçiniz...</option>
                {data?.departmanlar?.map((d) => (
                  <option key={d.departman_id} value={d.departman_id}>
                    {d.departman_adi}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Pozisyon (Maaş Otomatik)</label>
              <select name="pozisyon_id" className="input" required>
                <option value="">Seçiniz...</option>
                {data?.pozisyonlar?.map((p) => (
                  <option key={p.pozisyon_id} value={p.pozisyon_id}>
                    {p.pozisyon_adi} (Taban: {p.taban_maas ? Number(p.taban_maas).toLocaleString('tr-TR') + ' ₺' : '-'})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="card mt-6">
          <div className="p-6 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-emerald-600">3. Kullanıcı Hesabı</h2>
            <p className="text-sm text-slate-500 mt-2">Personel için oturum açma hesabı oluşturmak zorunludur.</p>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="label">Kullanıcı Adı</label>
              <input name="kullanici_adi" className="input" required />
            </div>

            <div>
              <label className="label">Şifre</label>
              <input name="sifre" type="password" className="input" required />
            </div>

            <div>
              <label className="label">Rol</label>
              <select name="rol" className="input" defaultValue="employee" required>
                <option value="employee">Employee</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/admin/employees')}
            className="btn btn-secondary"
          >
            İptal
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-success px-8"
          >
            {isSubmitting ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </div>
      </form>
    </div>
  )
}
