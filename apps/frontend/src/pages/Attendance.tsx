import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Check, X, Umbrella, Save } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'
import type { AttendanceRecord } from '../types'
import { SkeletonTable, Avatar } from '../components/ui'

export default function Attendance() {
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [statuses, setStatuses] = useState<Record<number, string>>({})
  const [overtimes, setOvertimes] = useState<Record<number, number>>({})

  const { data, isLoading } = useQuery<{ personeller: AttendanceRecord[] } | null>({
    queryKey: ['attendance', selectedDate],
    queryFn: async () => {
      const response = await api.get(`/attendance?tarih=${selectedDate}`)
      return response.data
    },
  })

  const saveMutation = useMutation({
    mutationFn: (payload: any) => api.post('/attendance', payload),
    onSuccess: () => {
      toast.success('Yoklama kaydedildi')
      queryClient.invalidateQueries({ queryKey: ['attendance'] })
    },
  })

  const employees = data?.personeller || []

  const getStatus = (personel_id: number, currentStatus: string | null) => {
    if (statuses[personel_id] !== undefined) {
      return statuses[personel_id]
    }
    return currentStatus || 'Normal'
  }

  const handleStatusChange = (personel_id: number, status: string) => {
    setStatuses((prev) => ({ ...prev, [personel_id]: status }))
  }

  const getOvertime = (personel_id: number, current: number | null) => {
    if (overtimes[personel_id] !== undefined) return overtimes[personel_id]
    return current || 0
  }

  const handleOvertimeChange = (personel_id: number, hours: number) => {
    setOvertimes((prev) => ({ ...prev, [personel_id]: hours }))
  }

  const handleSave = () => {
    const kayitlar = employees.map((emp) => ({
      personel_id: emp.personel_id,
      durum: getStatus(emp.personel_id, emp.bugunku_durum),
      ek_mesai_saat: getOvertime(emp.personel_id, (emp as any).ek_mesai_saat || 0),
    }))

    saveMutation.mutate({ tarih: selectedDate, kayitlar })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Günlük Yoklama</h1>
            <p className="text-slate-500 mt-1">Yükleniyor...</p>
          </div>
        </div>
        <SkeletonTable rows={8} columns={4} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Günlük Yoklama</h1>
          <p className="text-slate-500 mt-1">
            Personel katılım durumunu işaretleyin
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-4 py-2">
            <Calendar size={20} className="text-slate-500" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => {
                setSelectedDate(e.target.value)
                setStatuses({})
                setOvertimes({})
              }}
              className="border-0 bg-transparent focus:outline-none font-medium"
            />
          </div>
        </div>
      </div>
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Personel
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Departman
                </th>
                <th className="text-center py-4 px-6 text-sm font-medium text-slate-600">
                  Durum Seçimi
                </th>
                <th className="text-center py-4 px-6 text-sm font-medium text-slate-600">
                  Ek Mesai (saat)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {employees.map((emp) => (
                <tr key={emp.personel_id} className="hover:bg-slate-50">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <Avatar name={`${emp.ad} ${emp.soyad}`} size="md" />
                      <div>
                        <p className="font-medium text-slate-900">
                          {emp.ad} {emp.soyad}
                        </p>
                        <p className="text-xs text-slate-500">{emp.tc_kimlik_no}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="badge bg-slate-100 text-slate-700">
                      {emp.departman_adi || '-'}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex justify-center gap-2">
                      <StatusButton
                        active={getStatus(emp.personel_id, emp.bugunku_durum) === 'Normal'}
                        onClick={() => handleStatusChange(emp.personel_id, 'Normal')}
                        color="success"
                        icon={<Check size={16} />}
                        label="Var"
                      />
                      <StatusButton
                        active={getStatus(emp.personel_id, emp.bugunku_durum) === 'Izinli'}
                        onClick={() => handleStatusChange(emp.personel_id, 'Izinli')}
                        color="warning"
                        icon={<Umbrella size={16} />}
                        label="İzin"
                      />
                      <StatusButton
                        active={getStatus(emp.personel_id, emp.bugunku_durum) === 'Devamsiz'}
                        onClick={() => handleStatusChange(emp.personel_id, 'Devamsiz')}
                        color="danger"
                        icon={<X size={16} />}
                        label="Yok"
                      />
                    </div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <input
                      type="number"
                      min={0}
                      step={0.25}
                      value={getOvertime(emp.personel_id, (emp as any).ek_mesai_saat || 0)}
                      onChange={(e) => handleOvertimeChange(emp.personel_id, Number(e.target.value))}
                      className="input w-28 text-center"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {employees.length === 0 && (
          <div className="py-12 text-center text-slate-500">
            Aktif personel bulunamadı
          </div>
        )}
        <div className="border-t border-slate-200 p-4 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="btn btn-primary"
          >
            <Save size={18} />
            {saveMutation.isPending ? 'Kaydediliyor...' : 'Seçimleri Kaydet'}
          </button>
        </div>
      </div>
    </div>
  )
}

interface StatusButtonProps {
  active: boolean
  onClick: () => void
  color: 'success' | 'warning' | 'danger'
  icon: React.ReactNode
  label: string
}

function StatusButton({ active, onClick, color, icon, label }: StatusButtonProps) {
  const colorClasses = {
    success: active
      ? 'bg-emerald-600 text-white border-emerald-600'
      : 'bg-white text-emerald-600 border-emerald-300 hover:bg-emerald-50',
    warning: active
      ? 'bg-amber-500 text-white border-amber-500'
      : 'bg-white text-amber-600 border-amber-300 hover:bg-amber-50',
    danger: active
      ? 'bg-red-600 text-white border-red-600'
      : 'bg-white text-red-600 border-red-300 hover:bg-red-50',
  }

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-4 py-2 rounded-lg border font-medium text-sm transition-all ${colorClasses[color]}`}
    >
      {icon}
      {label}
    </button>
  )
}
