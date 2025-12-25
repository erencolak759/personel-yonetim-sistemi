import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Fingerprint, User as UserIcon, Lock, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!username || !password) {
      setError('Kullanıcı adı ve şifre gereklidir')
      return
    }

    setIsLoading(true)

    try {
      const user = await login(username, password)
      if (user) {
        toast.success('Giriş başarılı!')
        if (user.ilk_giris) {
          navigate('/change-password')
        } else if (user.rol === 'admin') {
          navigate('/admin/dashboard')
        } else {
          navigate('/user/dashboard')
        }
      } else {
        setError('Geçersiz kullanıcı adı veya şifre')
      }
    } catch {
      setError('Giriş yapılırken bir hata oluştu')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-primary-950 to-slate-900 relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-700/20 via-transparent to-transparent" />
        <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Decorative elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl" />

      {/* Login card */}
      <div className="relative w-full max-w-md px-6">
        <div className="bg-white rounded-2xl shadow-2xl p-8 animate-fade-in">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl mb-4 shadow-lg shadow-primary-500/25">
              <Fingerprint size={32} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">HR Portal</h1>
            <p className="text-slate-500 mt-1 text-sm">Personel Yönetim Sistemi</p>
          </div>

          {/* Error alert */}
          {error && (
            <div className="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg flex items-center gap-3 text-error-700 animate-fade-in">
              <AlertCircle size={20} className="shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Kullanıcı Adı"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Kullanıcı adınız"
              leftIcon={<UserIcon size={18} />}
              autoComplete="username"
            />

            <Input
              label="Şifre"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              leftIcon={<Lock size={18} />}
              autoComplete="current-password"
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full"
            >
              Oturum Aç
            </Button>
          </form>

          {/* Application link */}
          <div className="mt-6 text-center">
            <Link
              to="/apply"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
            >
              İş Başvurusu Yap →
            </Link>
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-slate-200 text-center">
            <p className="text-xs text-slate-400">
              © 2025 Marmara Yönetim A.Ş. Tüm hakları saklıdır.
            </p>
          </div>
        </div>

        {/* Help text */}
        <p className="text-center text-slate-400 text-xs mt-6">
          Giriş sorunu yaşıyorsanız IT departmanı ile iletişime geçin.
        </p>
      </div>
    </div>
  )
}
