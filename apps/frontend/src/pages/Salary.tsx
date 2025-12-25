import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Wallet, Printer } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import type { Salary as SalaryType } from '../types'
import PayrollPreview from '../components/PayrollPreview'
import { SkeletonTable } from '../components/ui'

export default function Salary() {
  const { data, isLoading } = useQuery<{ maaslar: SalaryType[] }>({
    queryKey: ['salary'],
    queryFn: async () => {
      const response = await api.get('/salary')
      return { maaslar: response.data }
    },
  })

  const queryClient = useQueryClient()
  const [period, setPeriod] = useState<string>(new Date().toISOString().slice(0, 7))
  const [preview, setPreview] = useState<any[] | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  const generateMutation = useMutation({
    mutationFn: async (payload: any) => {
      return api.post('/salary/generate', payload)
    },
    onSuccess: (res) => {
      toast.success(res.data?.message || 'Bordrolar oluşturuldu')
      queryClient.invalidateQueries({ queryKey: ['salary'] })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Bordro oluşturma hatası')
    }
  })

  const downloadPayrollsPdf = async () => {
    try {
      const [y, m] = period.split('-').map(Number)
      const res = await api.get('/salary/pdf', {
        params: { yil: y, ay: m },
        responseType: 'blob',
      })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `bordro_toplu_${m}_${y}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'PDF indirme hatası')
    }
  }

  const salaries = data?.maaslar || []

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Maaş Bordrosu</h1>
            <p className="text-slate-500 mt-1">Yükleniyor...</p>
          </div>
        </div>
        <SkeletonTable rows={6} columns={6} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Maaş Bordrosu</h1>
          <p className="text-slate-500 mt-1">Personel maaş kayıtları</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="month"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="input"
          />
          <button
            type="button"
            onClick={() => {
              const [y, m] = period.split('-').map(Number)
              generateMutation.mutate({ yil: y, ay: m })
            }}
            disabled={generateMutation.isPending}
            className="btn btn-primary inline-flex w-auto items-center gap-2 h-10 px-4 transition-all duration-150"
          >
            <Wallet size={18} />
            <span className="whitespace-nowrap">
              {generateMutation.isPending ? 'Oluşturuluyor...' : 'Bordro Oluştur'}
            </span>
          </button>
          <button
            type="button"
            onClick={async () => {
              try {
                setPreviewLoading(true)
                const [y, m] = period.split('-').map(Number)
                const res = await api.post('/salary/preview', { yil: y, ay: m })
                setPreview(res.data?.previews || null)
              } catch (err: any) {
                toast.error(err?.response?.data?.error || 'Önizleme hatası')
              }
              finally {
                setPreviewLoading(false)
              }
            }}
            className="btn btn-secondary flex items-center gap-2 h-10"
          >
            {previewLoading ? 'Önizleniyor...' : 'Önizleme'}
          </button>
          <button
            type="button"
            onClick={downloadPayrollsPdf}
            className="btn btn-outline inline-flex items-center gap-2 h-10 px-4 transition-all duration-150 whitespace-nowrap"
          >
            <Printer size={18} />
            <span className="inline-block">PDF İndir</span>
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Dönem</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Personel</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Brüt Maaş</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Eklemeler</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Kesintiler</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Net Ödenen</th>
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

      {preview && (
        <div className="mt-4">
          <PayrollPreview previews={preview} period={period} />
        </div>
      )}
    </div>
  )
}
