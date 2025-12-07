import { useQuery } from '@tanstack/react-query'
import { Wallet, Printer } from 'lucide-react'
import api from '../lib/api'
import type { Salary as SalaryType } from '../types'

export default function Salary() {
  const { data, isLoading } = useQuery<{ maaslar: SalaryType[] }>({
    queryKey: ['salary'],
    queryFn: async () => {
      const response = await api.get('/salary')
      return { maaslar: response.data }
    },
  })

  const salaries = data?.maaslar || []

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
          <h1 className="text-2xl font-bold text-slate-900">Maaş Bordrosu</h1>
          <p className="text-slate-500 mt-1">Personel maaş kayıtları</p>
        </div>
        <button onClick={() => window.print()} className="btn btn-outline">
          <Printer size={18} />
          PDF / Yazdır
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Dönem
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Personel
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Brüt Maaş
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Eklemeler
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Kesintiler
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Net Ödenen
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Durum
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {salaries.map((salary) => (
                <tr key={salary.maas_hesap_id} className="hover:bg-slate-50">
                  <td className="py-4 px-6 font-medium text-slate-700">
                    {salary.donem_ay}/{salary.donem_yil}
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-cyan-100 text-cyan-700 flex items-center justify-center font-semibold">
                        {salary.ad[0]}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">
                          {salary.ad} {salary.soyad}
                        </p>
                        <p className="text-xs text-slate-500">
                          {salary.departman_adi || '-'}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-900">
                    {salary.brut_maas.toLocaleString('tr-TR')} ₺
                  </td>
                  <td className="py-4 px-6 text-sm text-emerald-600">
                    +{salary.toplam_ekleme.toLocaleString('tr-TR')} ₺
                  </td>
                  <td className="py-4 px-6 text-sm text-red-600">
                    -{salary.toplam_kesinti.toLocaleString('tr-TR')} ₺
                  </td>
                  <td className="py-4 px-6 font-bold text-lg text-slate-900">
                    {salary.net_maas.toLocaleString('tr-TR')} ₺
                  </td>
                  <td className="py-4 px-6">
                    <span
                      className={`badge ${
                        salary.odendi_mi ? 'badge-success' : 'badge-warning'
                      }`}
                    >
                      {salary.odendi_mi ? 'Ödendi' : 'Bekliyor'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {salaries.length === 0 && (
          <div className="py-12 text-center">
            <Wallet className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 text-slate-500">
              Kayıtlı maaş bordrosu bulunamadı
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
