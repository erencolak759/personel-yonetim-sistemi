import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Wallet, CalendarClock } from 'lucide-react'
import api from '../lib/api'
import type { Salary } from '../types'

const monthNames = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']

function formatPeriod(year: number, month: number) {
  const name = monthNames[month - 1] || `${month}. Ay`
  return `${name} ${year}`
}

function formatCurrency(value?: number | null) {
  if (value === null || value === undefined) return '-'
  return `₺${Number(value).toLocaleString('tr-TR')}`
}

export default function UserPayroll() {
  const { data, isLoading } = useQuery<Salary[]>({
    queryKey: ['my-salaries'],
    queryFn: async () => {
      const res = await api.get('/salary')
      return res.data
    },
  })

  const sortedSalaries = useMemo(() => {
    if (!data) return []
    return [...data].sort((a, b) => {
      if (a.donem_yil === b.donem_yil) return b.donem_ay - a.donem_ay
      return b.donem_yil - a.donem_yil
    })
  }, [data])

  const latestSalary = sortedSalaries[0]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Bordro</h1>
        <p className="text-slate-500 mt-1">Kendinize ait maaş bordrolarınız.</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-primary-50 text-primary-600">
            <Wallet size={22} />
          </div>
          <div>
            <p className="text-sm text-slate-500">Son Bordro</p>
            <p className="text-lg font-semibold text-slate-900">
              {latestSalary ? formatPeriod(latestSalary.donem_yil, latestSalary.donem_ay) : 'Henüz bordro yok'}
            </p>
          </div>
        </div>
        {latestSalary ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-sm text-slate-500">Net Ödeme</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(latestSalary.net_maas)}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-sm text-slate-500">Brüt Maaş</p>
              <p className="text-xl font-semibold text-slate-900 mt-1">{formatCurrency(latestSalary.brut_maas)}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-sm text-slate-500">Durum</p>
              <span
                className={`inline-flex mt-1 items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                  latestSalary.odendi_mi ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                }`}
              >
                <CalendarClock size={16} />
                {latestSalary.odendi_mi ? 'Ödendi' : 'Ödeme Bekliyor'}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-slate-500 text-sm">Henüz bordro kaydı bulunmuyor.</p>
        )}
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CalendarClock size={18} className="text-primary-600" />
            <h3 className="text-lg font-semibold text-slate-900">Tüm Bordrolar</h3>
          </div>
          <p className="text-xs text-slate-500">Son kayıtlar en üstte</p>
        </div>

        {sortedSalaries.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Dönem</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Net Ödeme</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sortedSalaries.map((salary) => (
                  <tr key={salary.maas_hesap_id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-sm font-medium text-slate-900">
                      {formatPeriod(salary.donem_yil, salary.donem_ay)}
                    </td>
                    <td className="py-3 px-4 text-sm text-emerald-700 font-semibold">
                      {formatCurrency(salary.net_maas)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge ${salary.odendi_mi ? 'badge-success' : 'badge-warning'}`}>
                        {salary.odendi_mi ? 'Ödendi' : 'Bekliyor'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-slate-500 text-sm">Gösterilecek bordro bulunamadı.</p>
        )}
      </div>
    </div>
  )
}

