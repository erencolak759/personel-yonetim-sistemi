import { useQuery } from '@tanstack/react-query'
import { Users, Umbrella, Wallet, Clock, ArrowUp, ArrowDown, Megaphone, UserPlus } from 'lucide-react'
import api from '../lib/api'
import type { DashboardStats } from '../types'

interface DashboardData {
  stats: DashboardStats
  departman_data: { departman_adi: string; sayi: number }[]
  devamsizlik_data: { ay: string; sayi: number }[]
  izin_stats: { onay_durumu: string; sayi: number }[]
  maas_dept_data: { departman_adi: string; ort_maas: number }[]
  duyurular: { duyuru_id: number; baslik: string; icerik: string; yayin_tarihi: string | null; oncelik: string }[]
  adaylar: { aday_id: number; ad: string; soyad: string; basvuru_tarihi: string | null; durum: string; pozisyon_adi: string }[]
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

  const izinStatsNormalized =
    ['Onaylandi', 'Beklemede', 'Reddedildi'].map((key) => {
      const found = data?.izin_stats?.find((s) => s.onay_durumu === key)
      return { onay_durumu: key, sayi: found?.sayi || 0 }
    })

  const izinToplam = izinStatsNormalized.reduce((acc, i) => acc + (i.sayi || 0), 0)

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
          trend={`${(stats as any).personel_artis_oran?.toFixed?.(1) ?? '0.0'}%`}
          trendUp={(stats as any).personel_artis_oran >= 0}
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
          value={`₺${Number((stats as any).odenen_maas || 0).toLocaleString('tr-TR')}`}
          icon={Wallet}
          subtitle={`Bütçe: %${Number((stats as any).maas_butce_oran || 0).toFixed(0)}`}
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
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {izinStatsNormalized.map((stat) => {
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

      {/* Alt bölüm: grafik + son duyurular + son adaylar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            İzin Durumu (Pasta Grafik)
          </h3>
          {izinToplam > 0 ? (
            <div className="flex items-center gap-6">
              <div className="relative w-32 h-32">
                {(() => {
                  const findValue = (key: string) =>
                    izinStatsNormalized.find((s) => s.onay_durumu === key)?.sayi || 0
                  const onay = findValue('Onaylandi')
                  const bekle = findValue('Beklemede')
                  const red = findValue('Reddedildi')
                  const total = onay + bekle + red || 1
                  const onayPct = (onay / total) * 100
                  const beklePct = (bekle / total) * 100
                  const redPct = (red / total) * 100

                  const gradient = `conic-gradient(
                    rgba(16, 185, 129, 0.9) 0 ${onayPct}%,
                    rgba(245, 158, 11, 0.9) ${onayPct}% ${onayPct + beklePct}%,
                    rgba(239, 68, 68, 0.9) ${onayPct + beklePct}% 100%
                  )`

                  return (
                    <>
                      <div
                        className="w-full h-full rounded-full"
                        style={{ backgroundImage: gradient }}
                      />
                      <div className="absolute inset-4 bg-white rounded-full flex items-center justify-center">
                        <span className="text-sm font-semibold text-slate-700">
                          {izinToplam} izin
                        </span>
                      </div>
                    </>
                  )
                })()}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-slate-700">Onaylanan</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-amber-500" />
                  <span className="text-slate-700">Bekleyen</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="text-slate-700">Reddedilen</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-6">
              Henüz izin verisi bulunmuyor.
            </p>
          )}
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Megaphone size={18} className="text-primary-600" />
            Son Duyurular
          </h3>
              <div className="space-y-3">
                {data?.duyurular?.map((d) => (
                  <div key={d.duyuru_id} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-slate-900 line-clamp-1">{d.baslik}</p>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          d.oncelik === 'Yuksek'
                            ? 'bg-red-100 text-red-700'
                            : d.oncelik === 'Dusuk'
                            ? 'bg-slate-100 text-slate-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {d.oncelik}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{d.icerik}</p>
                    {d.yayin_tarihi && (
                      <p className="text-[11px] text-slate-400 mt-1">{d.yayin_tarihi}</p>
                    )}
                  </div>
                ))}
            {(!data?.duyurular || data.duyurular.length === 0) && (
              <p className="text-slate-500 text-sm text-center py-4">
                Henüz duyuru bulunmuyor
              </p>
            )}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <UserPlus size={18} className="text-primary-600" />
            Son Adaylar
          </h3>
          <div className="space-y-3">
            {data?.adaylar?.map((a) => (
              <div
                key={a.aday_id}
                className="border border-slate-200 rounded-lg p-3 bg-slate-50 max-w-xs"
              >
                <p className="text-sm font-medium text-slate-900">
                  {a.ad} {a.soyad}
                </p>
                <p className="text-xs text-slate-600 mt-0.5">{a.pozisyon_adi}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Başvuru: {a.basvuru_tarihi || '-'}
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Durum: {a.durum}
                </p>
              </div>
            ))}
            {(!data?.adaylar || data.adaylar.length === 0) && (
              <p className="text-slate-500 text-sm text-center py-4">
                Henüz aday bulunmuyor
              </p>
            )}
          </div>
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
