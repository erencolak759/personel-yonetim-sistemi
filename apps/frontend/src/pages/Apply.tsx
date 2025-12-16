import { useEffect, useState } from 'react'
import api from '../lib/api'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

type Position = { pozisyon_id: number; pozisyon_adi: string }

export default function Apply() {
  const navigate = useNavigate()
  const [positions, setPositions] = useState<Position[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [form, setForm] = useState({
    ad: '',
    soyad: '',
    email: '',
    telefon: '',
    pozisyon_id: '',
  })

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/candidates/positions')
        setPositions(res.data || [])
      } catch {
        toast.error('Pozisyonlar alınamadı')
      }
    }
    load()
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.ad || !form.soyad || !form.pozisyon_id) {
      toast.error('Ad, Soyad ve Pozisyon zorunlu')
      return
    }
    setIsSubmitting(true)
    try {
      await api.post('/candidates/apply', {
        ...form,
        pozisyon_id: Number(form.pozisyon_id),
      })
      toast.success('Başvurunuz alındı. Teşekkürler!')
      navigate('/login')
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'Başvuru gönderilemedi')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-2xl">
        <div className="card p-6">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">İşe Başvuru</h1>
          <p className="text-slate-500 mb-6">Bilgilerinizi doldurun, başvurunuz HR ekibine iletilsin.</p>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Ad</label>
                <input name="ad" value={form.ad} onChange={handleChange} className="input" required />
              </div>
              <div>
                <label className="label">Soyad</label>
                <input name="soyad" value={form.soyad} onChange={handleChange} className="input" required />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">E-posta</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  className="input"
                  placeholder="ornek@firma.com"
                />
              </div>
              <div>
                <label className="label">Telefon</label>
                <input
                  name="telefon"
                  value={form.telefon}
                  onChange={handleChange}
                  className="input"
                  placeholder="05xx..."
                />
              </div>
            </div>

            <div>
              <label className="label">Pozisyon</label>
              <select
                name="pozisyon_id"
                value={form.pozisyon_id}
                onChange={handleChange}
                className="input"
                required
              >
                <option value="">Seçiniz</option>
                {positions.map((p) => (
                  <option key={p.pozisyon_id} value={p.pozisyon_id}>
                    {p.pozisyon_adi}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-between items-center pt-2">
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="btn btn-secondary"
              >
                Geri
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn btn-primary"
              >
                {isSubmitting ? 'Gönderiliyor...' : 'Başvuruyu Tamamla'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}


