import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { KeyRound, RefreshCw, Eye, EyeOff } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'

type UserRow = {
  personel_id: number
  ad: string
  soyad: string
  personel_email: string | null
  personel_telefon: string | null
  departman_adi: string | null
  kullanici_id: number | null
  kullanici_adi: string | null
  email: string | null
  rol: string | null
  aktif_mi: number | boolean | null
  son_giris: string | null
  ilk_giris?: number | boolean | null
}

function generatePassword(length = 10) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*'
  let result = ''
  const array = new Uint32Array(length)
  window.crypto.getRandomValues(array)
  for (let i = 0; i < length; i++) {
    result += chars[array[i] % chars.length]
  }
  return result
}

export default function Users() {
  const queryClient = useQueryClient()
  const [resettingId, setResettingId] = useState<number | null>(null)
  const [revealedPasswords, setRevealedPasswords] = useState<Record<number, string>>({})
  const [showPasswordId, setShowPasswordId] = useState<number | null>(null)

  const { data, isLoading } = useQuery<UserRow[]>({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await api.get('/users')
      return res.data
    },
  })

  const resetMutation = useMutation({
    mutationFn: async (user: UserRow) => {
      if (!user.kullanici_id) throw new Error('Bu personelin kullanıcı hesabı yok')
      const newPassword = generatePassword()
      const res = await api.put(`/users/${user.kullanici_id}`, { sifre: newPassword })
      const returnedPassword = res.data?.password || newPassword
      return { user, password: returnedPassword }
    },
    onMutate: (user) => setResettingId(user.kullanici_id || null),
    onSuccess: ({ user, password }) => {
      toast.success(`Şifre hazır (${user.kullanici_adi || user.ad}).`)
      // After admin reset, show the returned password immediately (backend sets ilk_giris=1)
      setRevealedPasswords((prev) => {
        const next = user.kullanici_id ? { ...prev, [user.kullanici_id]: password } : prev
        try {
          sessionStorage.setItem('revealedPasswords', JSON.stringify(next))
        } catch {}
        return next
      })
      if (user.kullanici_id) {
        setShowPasswordId(user.kullanici_id)
        try {
          sessionStorage.setItem('revealedPasswordVisibleId', String(user.kullanici_id))
        } catch {}
      }
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Şifre sıfırlanamadı')
    },
    onSettled: () => setResettingId(null),
  })

  const users = data || []

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem('revealedPasswords')
      if (stored) setRevealedPasswords(JSON.parse(stored))
      const visible = sessionStorage.getItem('revealedPasswordVisibleId')
      if (visible) setShowPasswordId(Number(visible))
    } catch {}
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Kullanıcı Hesapları</h1>
          <p className="text-slate-500 mt-1">
            Tüm kullanıcı adlarını görüntüleyin, gerektiğinde şifre sıfırlayın.
          </p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Kullanıcı Adı</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Ad Soyad</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">E-posta</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Rol</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Durum</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Son Giriş</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Şifre Göster</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-slate-600">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.personel_id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 text-sm font-medium text-slate-900">
                    {u.kullanici_adi || '-'}
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-700">
                    {`${u.ad || ''} ${u.soyad || ''}`.trim() || '-'}
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-600">
                    {u.email || u.personel_email || '-'}
                  </td>
                  <td className="py-3 px-4 text-sm">
                    <span className="badge bg-slate-100 text-slate-700 capitalize">
                      {u.rol || '-'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm">
                    <span
                      className={`badge ${
                        u.aktif_mi ? 'badge-success' : 'badge-warning'
                      }`}
                    >
                      {u.kullanici_id ? (u.aktif_mi ? 'Aktif' : 'Pasif') : 'Hesap Yok'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-500">
                    {u.son_giris ? new Date(u.son_giris).toLocaleString('tr-TR') : '-'}
                  </td>
                  <td className="py-3 px-4 text-sm">
                    {u.kullanici_id ? (
                      <div className="inline-flex items-center gap-2">
                        <div className="inline-flex items-center gap-2">
                          {u.ilk_giris === 0 ? (
                            <button
                              type="button"
                              className="btn btn-ghost px-2 py-1 text-xs inline-flex items-center gap-1 opacity-50 cursor-not-allowed"
                              title="Kullanıcı şifresini güncellediği için görüntülenemez"
                              disabled
                            >
                              <Eye size={14} />
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="btn btn-ghost px-2 py-1 text-xs inline-flex items-center gap-1"
                              onClick={() => {
                                const next = showPasswordId === u.kullanici_id ? null : u.kullanici_id
                                setShowPasswordId(next)
                                try {
                                  if (next) sessionStorage.setItem('revealedPasswordVisibleId', String(next))
                                  else sessionStorage.removeItem('revealedPasswordVisibleId')
                                } catch {}
                              }}
                              title="Şifreyi göster/gizle"
                            >
                              {showPasswordId === u.kullanici_id ? <EyeOff size={14} /> : <Eye size={14} />}
                            </button>
                          )}

                          <button
                            type="button"
                            className="btn btn-ghost px-2 py-1 text-xs inline-flex items-center gap-1"
                            onClick={() => resetMutation.mutate(u)}
                            title="Şifreyi sıfırla"
                            disabled={resettingId === u.kullanici_id}
                          >
                            {resettingId === u.kullanici_id ? (
                              <RefreshCw size={14} className="animate-spin" />
                            ) : (
                              <KeyRound size={14} />
                            )}
                          </button>

                          {showPasswordId === u.kullanici_id && revealedPasswords[u.kullanici_id] && (
                            <span className="text-xs text-slate-700 bg-slate-100 rounded px-2 py-1">
                              {revealedPasswords[u.kullanici_id]}
                            </span>
                          )}
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">Hesap yok</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex justify-end gap-2">
                      <span className="text-xs text-slate-400">—</span>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 text-sm">
                    Kayıtlı kullanıcı bulunamadı.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}


