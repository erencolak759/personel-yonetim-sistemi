import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function ChangePassword() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { refresh, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    if (newPassword !== confirmPassword) {
      toast.error('Yeni şifreler eşleşmiyor')
      setIsLoading(false)
      return
    }

    try {
      const res = await api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword })
      toast.success(res.data.message || 'Şifre değiştirildi')
      if (res.data?.token) {
        localStorage.setItem('authToken', res.data.token)
      }
      if (res.data?.token) {
        localStorage.setItem('authToken', res.data.token)
      }
      await refresh()
      const me = (await api.get('/auth/me')).data?.user
      if (me?.rol === 'admin') {
        navigate('/admin/dashboard')
      } else {
        navigate('/user/leaves')
      }
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Şifre değiştirilirken hata oluştu'
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const inSettings = location.pathname.includes('/settings')
  const showFirstLoginNote = !!(user && (user as any).ilk_giris)

  if (inSettings) {
    return (
      <div className="card p-6">
        <h2 className="text-xl font-semibold mb-4">Şifre Değiştir</h2>
        {showFirstLoginNote && (
          <p className="text-sm text-slate-500 mb-4">İlk girişte şifrenizi değiştirmek zorundasınız.</p>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Mevcut Şifre</label>
            <input type="password" className="input" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div>
            <label className="label">Yeni Şifre</label>
            <input type="password" className="input" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div>
            <label className="label">Yeni Şifre (Tekrar)</label>
            <input type="password" className="input" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <div className="flex justify-end">
            <button className="btn btn-primary" type="submit" disabled={isLoading}>
              {isLoading ? 'Kaydediliyor...' : 'Şifreyi Güncelle'}
            </button>
          </div>
        </form>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-full max-w-md p-6 bg-white rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Şifre Değiştir</h2>
        {showFirstLoginNote && (
          <p className="text-sm text-slate-500 mb-4">İlk girişte şifrenizi değiştirmek zorundasınız.</p>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Mevcut Şifre</label>
            <input type="password" className="input" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div>
            <label className="label">Yeni Şifre</label>
            <input type="password" className="input" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div>
            <label className="label">Yeni Şifre (Tekrar)</label>
            <input type="password" className="input" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <button className="btn btn-primary w-full" type="submit" disabled={isLoading}>
            {isLoading ? 'Kaydediliyor...' : 'Şifreyi Güncelle'}
          </button>
        </form>
      </div>
    </div>
  )
}
