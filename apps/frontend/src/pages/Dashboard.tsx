import { useQuery } from '@tanstack/react-query'
import { Users, Umbrella, Wallet, Clock, ArrowUp, ArrowDown } from 'lucide-react'
import api from '../lib/api'
import type { DashboardStats } from '../types'

interface DashboardData {
  stats: DashboardStats
  departman_data: { departman_adi: string; sayi: number }[]
  devamsizlik_data: { ay: string; sayi: number }[]
  izin_stats: { onay_durumu: string; sayi: number }[]
  maas_dept_data: { departman_adi: string; ort_maas: number }[]
}

export default function Dashboard() {
  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await api.get('/dashboard')
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const stats = data?.stats || { toplam: 0, izinli: 0, kalan_calisan: 0, bekleyen: 0 }

  return (
    <div className="space-y-6">
      
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Hoş geldiniz! İşte günlük özet.</p>
      </div>

      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Toplam Personel"
          value={stats.toplam}
          icon={Users}
          trend="+5%"
          trendUp={true}
          color="primary"
        />
        <StatCard
          title="Bugün İzinli"
          value={stats.izinli}
          icon={Umbrella}
          subtitle={`Ofiste: ${stats.kalan_calisan} Kişi`}
          color="warning"
        />
        <StatCard
          title="Ödenen Maaş"
          value="₺145K"
          icon={Wallet}
          subtitle="Bütçe: %75"
          color="success"
        />
        <StatCard
          title="Bekleyen İşler"
          value={stats.bekleyen}
          icon={Clock}
          subtitle="İzin talepleri"
          color="danger"
        />
      </div>

      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Departman Dağılımı
          </h3>
          <div className="space-y-4">
            {data?.departman_data?.map((dept) => (
              <div key={dept.departman_adi} className="flex items-center gap-4">
                <div className="w-32 text-sm text-slate-600 truncate">
                  {dept.departman_adi}
                </div>
                <div className="flex-1">
                  <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{
                        width: `${(dept.sayi / (stats.toplam || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
                <div className="w-12 text-sm font-medium text-slate-900 text-right">
                  {dept.sayi}
                </div>
              </div>
            ))}
            {(!data?.departman_data || data.departman_data.length === 0) && (
              <p className="text-slate-500 text-sm text-center py-4">
                Henüz veri bulunmuyor
              </p>
            )}
          </div>
        </div>

        
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            İzin Durumları
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {data?.izin_stats?.map((stat) => {
              const getColor = (status: string) => {
                switch (status) {
                  case 'Onaylandi':
                    return 'bg-emerald-100 text-emerald-700'
                  case 'Beklemede':
                    return 'bg-amber-100 text-amber-700'
                  case 'Reddedildi':
                    return 'bg-red-100 text-red-700'
                  default:
                    return 'bg-slate-100 text-slate-700'
                }
              }
              const getLabel = (status: string) => {
                switch (status) {
                  case 'Onaylandi':
                    return 'Onaylanan'
                  case 'Beklemede':
                    return 'Bekleyen'
                  case 'Reddedildi':
                    return 'Reddedilen'
                  default:
                    return status
                }
              }
              return (
                <div
                  key={stat.onay_durumu}
                  className={`p-4 rounded-xl text-center ${getColor(stat.onay_durumu)}`}
                >
                  <div className="text-2xl font-bold">{stat.sayi}</div>
                  <div className="text-sm mt-1">{getLabel(stat.onay_durumu)}</div>
                </div>
              )
            })}
            {(!data?.izin_stats || data.izin_stats.length === 0) && (
              <p className="col-span-3 text-slate-500 text-sm text-center py-4">
                Henüz veri bulunmuyor
              </p>
            )}
          </div>
        </div>
      </div>

      
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Departman Bazlı Ortalama Maaş
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">
                  Departman
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-slate-600">
                  Ortalama Maaş
                </th>
              </tr>
            </thead>
            <tbody>
              {data?.maas_dept_data?.map((dept) => (
                <tr key={dept.departman_adi} className="border-b border-slate-100">
                  <td className="py-3 px-4 text-sm text-slate-900">
                    {dept.departman_adi}
                  </td>
                  <td className="py-3 px-4 text-sm text-right font-medium text-emerald-600">
                    ₺{(dept.ort_maas !== undefined && dept.ort_maas !== null) ? Number(dept.ort_maas).toLocaleString('tr-TR') : '-'}
                  </td>
                </tr>
              ))}
              {(!data?.maas_dept_data || data.maas_dept_data.length === 0) && (
                <tr>
                  <td colSpan={2} className="py-8 text-center text-slate-500 text-sm">
                    Henüz veri bulunmuyor
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

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ComponentType<{ size?: number; className?: string }>
  trend?: string
  trendUp?: boolean
  subtitle?: string
  color: 'primary' | 'warning' | 'success' | 'danger'
}

function StatCard({ title, value, icon: Icon, trend, trendUp, subtitle, color }: StatCardProps) {
  const colorClasses = {
    primary: 'bg-primary-100 text-primary-600',
    warning: 'bg-amber-100 text-amber-600',
    success: 'bg-emerald-100 text-emerald-600',
    danger: 'bg-red-100 text-red-600',
  }

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
          {trend && (
            <p className={`text-sm mt-2 flex items-center gap-1 ${trendUp ? 'text-emerald-600' : 'text-red-600'}`}>
              {trendUp ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
              {trend}
            </p>
          )}
          {subtitle && (
            <p className="text-sm text-slate-500 mt-2">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  )
}
