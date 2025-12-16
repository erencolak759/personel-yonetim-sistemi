import { useQuery } from '@tanstack/react-query'
import { Users, Umbrella, Wallet, Clock, ArrowUp, ArrowDown, Megaphone, UserPlus } from 'lucide-react'
import { Chart } from 'react-google-charts'
import api from '../lib/api'
import type { DashboardStats } from '../types'

interface DashboardData {
  stats: DashboardStats
  departman_data: { departman_adi: string; sayi: number }[]
  devamsizlik_data: { ay: string; sayi: number }[]
  ise_alim_aylik: { ay: string; sayi: number }[]
  izin_stats: { onay_durumu: string; sayi: number }[]
  izin_turu_gun: { izin_adi: string; toplam_gun: number }[]
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

  const iseAlimSerisi = data?.ise_alim_aylik || []
  const izinTuruSerisi = data?.izin_turu_gun || []

  const izinToplam = izinStatsNormalized.reduce((acc, i) => acc + (i.sayi || 0), 0)
  const izinTuruToplamGun = izinTuruSerisi.reduce((acc, i) => acc + (i.toplam_gun || 0), 0)

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
          Son 10 Yıl Yeni İşe Alımlar
        </h3>
        {iseAlimSerisi.length > 0 ? (
          <Chart
            chartType="ColumnChart"
            width="100%"
            height="260px"
            loader={<div>Yükleniyor...</div>}
            data={[
              ['Ay', 'Yeni Personel'],
              ...iseAlimSerisi.map((i) => [i.ay, i.sayi]),
            ]}
            options={{
              legend: { position: 'none' },
              colors: ['#3b82f6'],
              vAxis: { minValue: 0 },
              chartArea: { left: 40, right: 10, top: 10, bottom: 40 },
            }}
          />
        ) : (
          <p className="text-slate-500 text-sm text-center py-6">
            Henüz işe alım verisi bulunmuyor.
          </p>
        )}
      </div>

      {/* Alt bölüm: izin grafikleri + son duyurular + son adaylar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            İzin Durumu (Pasta Grafik)
          </h3>
          {izinToplam > 0 ? (
            <Chart
              chartType="PieChart"
              width="100%"
              height="260px"
              loader={<div>Yükleniyor...</div>}
              data={[
                ['Durum', 'Adet'],
                ...izinStatsNormalized.map((i) => [i.onay_durumu, i.sayi]),
              ]}
              options={{
                pieHole: 0.45,
                legend: { position: 'right' },
                slices: {
                  0: { color: '#10b981' }, // Onaylandi
                  1: { color: '#f59e0b' }, // Beklemede
                  2: { color: '#ef4444' }, // Reddedildi
                },
                chartArea: { left: 10, right: 10, top: 10, bottom: 10 },
              }}
            />
          ) : (
            <p className="text-slate-500 text-sm text-center py-6">
              Henüz izin verisi bulunmuyor.
            </p>
          )}
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            İzin Türüne Göre Kullanılan Günler
          </h3>
          {izinTuruSerisi.length > 0 && izinTuruToplamGun > 0 ? (
            <Chart
              chartType="PieChart"
              width="100%"
              height="260px"
              loader={<div>Yükleniyor...</div>}
              data={[
                ['İzin Türü', 'Gün'],
                ...izinTuruSerisi.map((i) => [i.izin_adi, i.toplam_gun]),
              ]}
              options={{
                pieHole: 0.45,
                legend: { position: 'right' },
                chartArea: { left: 10, right: 10, top: 10, bottom: 10 },
              }}
            />
          ) : (
            <p className="text-slate-500 text-sm text-center py-6">
              Henüz izin kullanımı verisi bulunmuyor.
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
