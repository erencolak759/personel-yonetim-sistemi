import { useState, useEffect } from 'react'
import api from '../../lib/api'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function Profile() {
  const { user, refresh } = useAuth()
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ ad: '', soyad: '', telefon: '', email: '', adres: '', dogum_tarihi: '' })

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const me = (await api.get('/auth/me')).data?.user
        const pid = me?.personel_id
        if (!pid) {
          toast.error('Personel bilgisi bulunamadı')
          setLoading(false)
          return
        }
        const res = await api.get(`/employees/${pid}`)
        const personel = res.data?.personel
        if (mounted && personel) {
          setForm({
            ad: personel.ad || '',
            soyad: personel.soyad || '',
            telefon: personel.telefon || '',
            email: personel.email || '',
            adres: personel.adres || '',
            dogum_tarihi: personel.dogum_tarihi || '',
          })
        }
      } catch (err: any) {
        toast.error('Bilgiler yüklenirken hata oluştu')
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const handleChange = (k: string, v: any) => setForm(prev => ({ ...prev, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.put('/employees/me', form)
      toast.success('Bilgileriniz güncellendi')
      await refresh()
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'Güncelleme başarısız')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-6">Yükleniyor...</div>

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-4">Hesap Bilgilerim</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Ad</label>
          <input className="input" value={form.ad} onChange={(e) => handleChange('ad', e.target.value)} />
        </div>
        <div>
          <label className="label">Soyad</label>
          <input className="input" value={form.soyad} onChange={(e) => handleChange('soyad', e.target.value)} />
        </div>
        <div>
          <label className="label">Telefon</label>
          <input className="input" value={form.telefon} onChange={(e) => handleChange('telefon', e.target.value)} />
        </div>
        <div>
          <label className="label">E-posta</label>
          <input type="email" className="input" value={form.email} onChange={(e) => handleChange('email', e.target.value)} />
        </div>
        <div>
          <label className="label">Adres</label>
          <input className="input" value={form.adres} onChange={(e) => handleChange('adres', e.target.value)} />
        </div>
        <div>
          <label className="label">Doğum Tarihi</label>
          <input type="date" className="input" value={form.dogum_tarihi} onChange={(e) => handleChange('dogum_tarihi', e.target.value)} />
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="submit" className="btn btn-primary">Kaydet</button>
        </div>
      </form>
    </div>
  )
}
