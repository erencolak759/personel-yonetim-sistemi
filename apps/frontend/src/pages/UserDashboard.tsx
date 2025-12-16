import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Megaphone, Info, Clock3, TrendingUp } from 'lucide-react'
import api from '../lib/api'
import type { Announcement, Salary } from '../types'

export default function UserHome() {
  const {
    data: announcements,
    isLoading: announcementsLoading,
  } = useQuery<Announcement[]>({
    queryKey: ['announcements'],
    queryFn: async () => {
      const res = await api.get('/announcements')
      return res.data
    },
  })

  const { data: salaries } = useQuery<Salary[]>({
    queryKey: ['my-salaries'],
    queryFn: async () => {
      const res = await api.get('/salary')
      return res.data
    },
  })

  const loading = announcementsLoading

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Hoş geldiniz</h1>
        <p className="text-slate-500 mt-1">Duyuruları ve maaş trendinizi hızlıca görün.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-xl bg-primary-50 text-primary-600">
                <Megaphone size={22} />
              </div>
              <div>
                <p className="text-sm text-slate-500">Duyurular</p>
                <p className="text-lg font-semibold text-slate-900">Güncel bilgiler</p>
              </div>
            </div>
            <div className="space-y-3">
              {announcements && announcements.length > 0 ? (
                announcements.map((ann) => (
                  <div key={ann.duyuru_id} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-slate-900 line-clamp-1">{ann.baslik}</p>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          ann.oncelik === 'Yuksek'
                            ? 'bg-red-100 text-red-700'
                            : ann.oncelik === 'Dusuk'
                            ? 'bg-slate-100 text-slate-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {ann.oncelik}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{ann.icerik}</p>
                    {ann.yayin_tarihi && (
                      <p className="text-[11px] text-slate-400 mt-1">{ann.yayin_tarihi}</p>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-sm">Henüz duyuru bulunmuyor.</p>
              )}
            </div>
          </div>

          <PayrollTrend salaries={salaries} />
        </div>

        <div className="space-y-4">
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-2">
              <Info size={18} className="text-primary-600" />
              <p className="text-sm font-semibold text-slate-900">Bilgilendirme</p>
            </div>
            <p className="text-sm text-slate-600">
              Güncel duyuruları takip edin, bordro ve izin işlemlerinizi hızlıca gerçekleştirin.
            </p>
          </div>

          <div className="card p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock3 size={18} className="text-primary-600" />
              <p className="text-sm font-semibold text-slate-900">Yaklaşan Tarihler</p>
            </div>
            <p className="text-sm text-slate-600">
              Önemli tarihler için İK departmanıyla iletişimde kalın. İzin ve bordro dönemlerini kontrol edin.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function PayrollTrend({ salaries }: { salaries: Salary[] | undefined }) {
  const lastSix = useMemo(() => {
    const sorted = (salaries || []).slice().sort((a, b) => {
      if (a.donem_yil === b.donem_yil) return a.donem_ay - b.donem_ay
      return a.donem_yil - b.donem_yil
    })
    return sorted.slice(-6)
  }, [salaries])

  const maxNet = Math.max(...lastSix.map((s) => s.net_maas || 0), 0)
  const minNet = Math.min(...lastSix.map((s) => s.net_maas || 0), 0)
  const range = Math.max(maxNet - minNet, 1)

  const points = lastSix.map((s, idx) => {
    const x = (idx / Math.max(lastSix.length - 1, 1)) * 100
    const y = 100 - ((s.net_maas - minNet) / range) * 100
    return `${x},${y}`
  })

  const areaPoints =
    points.length > 0
      ? `0,100 ${points.join(' ')} 100,100`
      : ''

  return (
    <div className="card p-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={18} className="text-primary-600" />
        <h3 className="text-lg font-semibold text-slate-900">Bordro Trend</h3>
      </div>
      {lastSix.length === 0 ? (
        <p className="text-sm text-slate-500">Henüz bordro verisi yok.</p>
      ) : (
        <div className="space-y-4">
          <div className="h-48 relative">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full">
              <defs>
                <linearGradient id="payrollArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(59,130,246,0.25)" />
                  <stop offset="100%" stopColor="rgba(59,130,246,0.05)" />
                </linearGradient>
              </defs>
              {areaPoints && <polygon points={areaPoints} fill="url(#payrollArea)" />}
              <polyline
                points={points.join(' ')}
                fill="none"
                stroke="rgb(59,130,246)"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              {lastSix.map((s, idx) => {
                const x = (idx / Math.max(lastSix.length - 1, 1)) * 100
                const y = 100 - ((s.net_maas - minNet) / range) * 100
                return <circle key={s.maas_hesap_id} cx={x} cy={y} r={1.8} fill="rgb(59,130,246)" />
              })}
            </svg>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
            {lastSix.map((s) => (
              <div key={`label-${s.maas_hesap_id}`} className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                <div className="text-xs text-slate-500">{s.donem_ay}/{s.donem_yil}</div>
                <div className="font-semibold text-slate-900">₺{Number(s.net_maas).toLocaleString('tr-TR')}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

