import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Check, X, Clock, Umbrella, Filter } from 'lucide-react'
import api from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'
import type { Leave, Employee, LeaveType } from '../types'

type FilterType = 'tumunu' | 'bekleyen' | 'onaylanan' | 'reddedilen'

export default function Leaves() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<FilterType>('tumunu')
  const [showAddModal, setShowAddModal] = useState(false)

  const { data, isLoading } = useQuery<{
    izinler: Leave[]
    personeller: Employee[]
    izin_turleri: LeaveType[]
  }>({
    queryKey: ['leaves', filter],
    queryFn: async () => {
      const response = await api.get(`/leaves?filtre=${filter}`)
      return { izinler: response.data, personeller: [], izin_turleri: [] }
    },
  })

  const { user } = useAuth()

  const employeesQuery = useQuery({
    queryKey: ['employees'],
    queryFn: async () => {
      const res = await api.get('/employees')
      return res.data || []
    },
  })

  const leaveTypesQuery = useQuery({
    queryKey: ['leave-types'],
    queryFn: async () => {
      const res = await api.get('/leave-types')
      return res.data || []
    },
  })

  const approveMutation = useMutation({
    mutationFn: (id: number) => api.post(`/leaves/${id}/approve`),
    onSuccess: () => {
      toast.success('İzin onaylandı')
      queryClient.invalidateQueries({ queryKey: ['leaves'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (id: number) => api.post(`/leaves/${id}/reject`),
    onSuccess: () => {
      toast.success('İzin reddedildi')
      queryClient.invalidateQueries({ queryKey: ['leaves'] })
    },
  })

  const addMutation = useMutation({
    mutationFn: (formData: FormData) => {
      const data = Object.fromEntries(formData)
      return api.post('/leaves', data)
    },
    onSuccess: () => {
      toast.success('İzin talebi oluşturuldu')
      queryClient.invalidateQueries({ queryKey: ['leaves'] })
      setShowAddModal(false)
    },
  })

  const leaves = data?.izinler || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">İzin Yönetimi</h1>
          <p className="text-slate-500 mt-1">
            Personel izin kayıtlarını takip edin
          </p>
        </div>
        {user?.rol !== 'admin' && (
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary"
          >
            <Plus size={18} />
            Yeni İzin Talebi
          </button>
        )}
      </div>

      {/* Filter Buttons */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-2">
          <FilterButton
            active={filter === 'tumunu'}
            onClick={() => setFilter('tumunu')}
            label={`Tümü (${leaves.length})`}
            icon={<Filter size={16} />}
          />
          <FilterButton
            active={filter === 'bekleyen'}
            onClick={() => setFilter('bekleyen')}
            label="Bekleyen"
            icon={<Clock size={16} />}
            color="warning"
          />
          <FilterButton
            active={filter === 'onaylanan'}
            onClick={() => setFilter('onaylanan')}
            label="Onaylanan"
            icon={<Check size={16} />}
            color="success"
          />
          <FilterButton
            active={filter === 'reddedilen'}
            onClick={() => setFilter('reddedilen')}
            label="Reddedilen"
            icon={<X size={16} />}
            color="danger"
          />
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Personel
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  İzin Türü
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Tarih Aralığı
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Süre
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Durum
                </th>
                <th className="text-right py-4 px-6 text-sm font-medium text-slate-600">
                  İşlemler
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {leaves.map((leave) => (
                <tr key={leave.izin_kayit_id} className="hover:bg-slate-50">
                  <td className="py-4 px-6 font-medium text-slate-900">
                    {leave.ad} {leave.soyad}
                  </td>
                  <td className="py-4 px-6">
                    <span className="badge badge-info">{leave.izin_adi}</span>
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-600">
                    <div>{leave.baslangic_tarihi}</div>
                    <div className="text-slate-400">{leave.bitis_tarihi}</div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="badge bg-slate-100 text-slate-700">
                      {leave.gun_sayisi} Gün
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span
                      className={`badge ${
                        leave.onay_durumu === 'Onaylandi'
                          ? 'badge-success'
                          : leave.onay_durumu === 'Reddedildi'
                          ? 'badge-danger'
                          : 'badge-warning'
                      }`}
                    >
                      {leave.onay_durumu === 'Onaylandi'
                        ? 'Onaylandı'
                        : leave.onay_durumu === 'Reddedildi'
                        ? 'Reddedildi'
                        : 'Beklemede'}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex justify-end gap-2">
                      {leave.onay_durumu === 'Beklemede' && (
                        <>
                          <button
                            onClick={() => approveMutation.mutate(leave.izin_kayit_id)}
                            className="btn btn-success text-sm py-1.5 px-3"
                            disabled={approveMutation.isPending}
                          >
                            <Check size={14} />
                            Onayla
                          </button>
                          <button
                            onClick={() => rejectMutation.mutate(leave.izin_kayit_id)}
                            className="btn btn-danger text-sm py-1.5 px-3"
                            disabled={rejectMutation.isPending}
                          >
                            <X size={14} />
                            Reddet
                          </button>
                        </>
                      )}
                      {leave.onay_durumu !== 'Beklemede' && (
                        <span className="text-sm text-slate-400">İşlem Tamamlandı</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {leaves.length === 0 && (
          <div className="py-12 text-center">
            <Umbrella className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 text-slate-500">
              {filter === 'bekleyen'
                ? 'Bekleyen izin talebi yok'
                : filter === 'onaylanan'
                ? 'Onaylanmış izin kaydı yok'
                : filter === 'reddedilen'
                ? 'Reddedilmiş izin kaydı yok'
                : 'Henüz izin kaydı yok'}
            </p>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900">
                Yeni İzin Talebi
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                addMutation.mutate(new FormData(e.currentTarget))
              }}
              className="p-6 space-y-4"
            >
              {user?.rol === 'admin' ? (
                <div>
                  <label className="label">Personel</label>
                  <select name="personel_id" className="input" required>
                    <option value="">Seçiniz...</option>
                    {employeesQuery.data?.map((p: any) => (
                      <option key={p.personel_id} value={p.personel_id}>
                        {p.ad} {p.soyad}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <input type="hidden" name="personel_id" value={user?.personel_id || ''} />
              )}
              <div>
                <label className="label">İzin Türü</label>
                <select name="izin_turu_id" className="input" required>
                  <option value="">Seçiniz...</option>
                  {leaveTypesQuery.data?.map((t: any) => (
                    <option key={t.izin_turu_id} value={t.izin_turu_id}>
                      {t.izin_adi}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Başlangıç</label>
                  <input
                    type="date"
                    name="baslangic_tarihi"
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="label">Bitiş</label>
                  <input
                    type="date"
                    name="bitis_tarihi"
                    className="input"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="label">Gün Sayısı (opsiyonel)</label>
                <input
                  type="number"
                  name="gun_sayisi"
                  className="input"
                  placeholder="Otomatik hesaplanacaksa boş bırakın"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn btn-secondary flex-1"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending}
                  className="btn btn-primary flex-1"
                >
                  {addMutation.isPending ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

interface FilterButtonProps {
  active: boolean
  onClick: () => void
  label: string
  icon: React.ReactNode
  color?: 'warning' | 'success' | 'danger'
}

function FilterButton({ active, onClick, label, icon, color }: FilterButtonProps) {
  const baseClass = active
    ? color === 'warning'
      ? 'bg-amber-500 text-white'
      : color === 'success'
      ? 'bg-emerald-500 text-white'
      : color === 'danger'
      ? 'bg-red-500 text-white'
      : 'bg-primary-600 text-white'
    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all ${baseClass}`}
    >
      {icon}
      {label}
    </button>
  )
}
