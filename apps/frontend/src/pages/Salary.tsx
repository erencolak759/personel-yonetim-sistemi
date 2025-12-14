import { useQuery } from '@tanstack/react-query'
import { Wallet, Printer, Download, Plus, FileText } from 'lucide-react'
import { useState, useEffect } from 'react'
import api from '../lib/api'
import type { Salary as SalaryType } from '../types'

// Modal Component (inline)
interface Employee {
  personel_id: number
  ad: string
  soyad: string
  departman_adi: string
}

interface SalaryCalculation {
  brut_maas: number
  toplam_ekleme: number
  toplam_kesinti: number
  net_maas: number
  detaylar: {
    sgk_isci: number
    gelir_vergisi: number
    damga_vergisi: number
    issizlik_isci: number
  }
}

function AddSalaryModal({ isOpen, onClose, onSuccess }: any) {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(false)
  const [calculating, setCalculating] = useState(false)

  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1

  const [formData, setFormData] = useState({
    personel_id: '',
    donem_yil: currentYear,
    donem_ay: currentMonth,
    brut_maas: '',
    eklemeler: {
      'Prim': '0',
      'Yemek Yardimi': '0',
      'Yol Yardimi': '0',
      'Fazla Mesai': '0',
    },
  })

  const [calculation, setCalculation] = useState<SalaryCalculation | null>(null)

  useEffect(() => {
  if (isOpen) {
    api.get('employees')  // ✅ ÇOĞUL!
      .then(res => {
        console.log('Personel listesi yüklendi:', res.data)
        setEmployees(res.data)
      })
      .catch(err => console.error('Personel hatası:', err))
  }}, [isOpen])

  const handleCalculate = async () => {
    if (!formData.brut_maas) {
      alert('Lütfen brüt maaş giriniz')
      return
    }

    setCalculating(true)
    try {
      const eklemeler: { [key: string]: number } = {}
      Object.entries(formData.eklemeler).forEach(([key, value]) => {
        const numValue = parseFloat(value) || 0
        if (numValue > 0) eklemeler[key] = numValue
      })

      const response = await api.post('/salary/calculate', {
        brut_maas: parseFloat(formData.brut_maas),
        eklemeler,
      })

      setCalculation(response.data)
    } catch (error) {
      console.error('Hesaplama hatası:', error)
      alert('Maaş hesaplanamadı')
    } finally {
      setCalculating(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.personel_id || !formData.brut_maas) {
      alert('Lütfen tüm zorunlu alanları doldurunuz')
      return
    }

    setLoading(true)
    try {
      const eklemeler: { [key: string]: number } = {}
      Object.entries(formData.eklemeler).forEach(([key, value]) => {
        const numValue = parseFloat(value) || 0
        if (numValue > 0) eklemeler[key] = numValue
      })

      await api.post('/salary', {
        personel_id: parseInt(formData.personel_id),
        donem_yil: formData.donem_yil,
        donem_ay: formData.donem_ay,
        brut_maas: parseFloat(formData.brut_maas),
        eklemeler,
      })

      alert('Bordro başarıyla oluşturuldu!')
      onSuccess()
      onClose()
      setFormData({
        personel_id: '',
        donem_yil: currentYear,
        donem_ay: currentMonth,
        brut_maas: '',
        eklemeler: {
          'Prim': '0',
          'Yemek Yardimi': '0',
          'Yol Yardimi': '0',
          'Fazla Mesai': '0',
        },
      })
      setCalculation(null)
    } catch (error: any) {
      console.error('Bordro oluşturma hatası:', error)
      alert('Hata: ' + (error.response?.data?.error || 'Bordro oluşturulamadı'))
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-900">Yeni Maaş Bordrosu</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-1">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Personel <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.personel_id}
                onChange={(e) => setFormData({ ...formData, personel_id: e.target.value })}
                className="input"
                required
              >
                <option value="">Seçiniz...</option>
                {employees.map((emp) => (
                  <option key={emp.personel_id} value={emp.personel_id}>
                    {emp.ad} {emp.soyad} - {emp.departman_adi}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Yıl *</label>
              <input
                type="number"
                value={formData.donem_yil}
                onChange={(e) => setFormData({ ...formData, donem_yil: parseInt(e.target.value) })}
                className="input"
                min="2020"
                max="2030"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Ay *</label>
              <select
                value={formData.donem_ay}
                onChange={(e) => setFormData({ ...formData, donem_ay: parseInt(e.target.value) })}
                className="input"
                required
              >
                {[...Array(12)].map((_, i) => (
                  <option key={i + 1} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Brüt Maaş (TL) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.brut_maas}
              onChange={(e) => setFormData({ ...formData, brut_maas: e.target.value })}
              className="input"
              placeholder="Örn: 25000"
              step="0.01"
              min="0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">Ek Ödemeler (İsteğe Bağlı)</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(formData.eklemeler).map((key) => (
                <div key={key}>
                  <label className="block text-xs text-slate-600 mb-1">{key}</label>
                  <input
                    type="number"
                    value={formData.eklemeler[key as keyof typeof formData.eklemeler]}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        eklemeler: { ...formData.eklemeler, [key]: e.target.value },
                      })
                    }
                    className="input"
                    placeholder="0"
                    step="0.01"
                    min="0"
                  />
                </div>
              ))}
            </div>
          </div>

          <div>
            <button
              type="button"
              onClick={handleCalculate}
              disabled={calculating || !formData.brut_maas}
              className="btn btn-outline w-full"
            >
              {calculating ? 'Hesaplanıyor...' : '🧮 Maaş Hesapla (Önizleme)'}
            </button>
          </div>

          {calculation && (
            <div className="bg-slate-50 rounded-lg p-4 space-y-3">
              <h3 className="font-semibold text-slate-900 mb-3">Hesaplama Sonucu</h3>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-slate-600">Brüt Maaş:</span>
                  <p className="font-semibold text-slate-900">{calculation.brut_maas.toLocaleString('tr-TR')} TL</p>
                </div>
                <div>
                  <span className="text-slate-600">Toplam Eklemeler:</span>
                  <p className="font-semibold text-emerald-600">+{calculation.toplam_ekleme.toLocaleString('tr-TR')} TL</p>
                </div>
                <div>
                  <span className="text-slate-600">Toplam Kesintiler:</span>
                  <p className="font-semibold text-red-600">-{calculation.toplam_kesinti.toLocaleString('tr-TR')} TL</p>
                </div>
                <div className="bg-primary-50 p-2 rounded">
                  <span className="text-primary-700 text-xs">Net Maaş:</span>
                  <p className="font-bold text-primary-900 text-lg">{calculation.net_maas.toLocaleString('tr-TR')} TL</p>
                </div>
              </div>

              <details className="mt-3">
                <summary className="cursor-pointer text-xs text-slate-600 hover:text-slate-900">Kesinti Detayları</summary>
                <div className="mt-2 space-y-1 text-xs text-slate-600 pl-4">
                  <div className="flex justify-between">
                    <span>SGK İşçi Payı:</span>
                    <span>{calculation.detaylar.sgk_isci.toLocaleString('tr-TR')} TL</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Gelir Vergisi:</span>
                    <span>{calculation.detaylar.gelir_vergisi.toLocaleString('tr-TR')} TL</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Damga Vergisi:</span>
                    <span>{calculation.detaylar.damga_vergisi.toLocaleString('tr-TR')} TL</span>
                  </div>
                  <div className="flex justify-between">
                    <span>İşsizlik Sigortası:</span>
                    <span>{calculation.detaylar.issizlik_isci.toLocaleString('tr-TR')} TL</span>
                  </div>
                </div>
              </details>
            </div>
          )}

          <div className="flex gap-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="btn btn-outline flex-1" disabled={loading}>
              İptal
            </button>
            <button type="submit" className="btn btn-primary flex-1" disabled={loading}>
              {loading ? 'Kaydediliyor...' : 'Bordro Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Main Component
export default function Salary() {
  const [isDownloading, setIsDownloading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data, isLoading, refetch } = useQuery<{ maaslar: SalaryType[] }>({
    queryKey: ['salary'],
    queryFn: async () => {
      const response = await api.get('/salary')
      return { maaslar: response.data }
    },
  })

  const salaries = data?.maaslar || []

  const handleDownloadPDF = async () => {
    setIsDownloading(true)

    try {
      const response = await api.get('/salary/pdf', {
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `maas_bordrosu_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(link)
      link.click()

      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      alert('PDF başarıyla indirildi!')
    } catch (error: any) {
      console.error('PDF indirme hatası:', error)
      alert('HATA: ' + (error.message || 'Bilinmeyen hata'))
    } finally {
      setIsDownloading(false)
    }
  }

  const handleDownloadSinglePDF = async (maasId: number, ad: string, soyad: string) => {
    try {
      const response = await api.get(`/salary/${maasId}/pdf`, {
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `bordro_${ad}_${soyad}.pdf`
      document.body.appendChild(link)
      link.click()

      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      console.error('PDF indirme hatası:', error)
      alert('PDF indirilemedi')
    }
  }

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
          <h1 className="text-2xl font-bold text-slate-900">Maaş Bordrosu</h1>
          <p className="text-slate-500 mt-1">Personel maaş kayıtları ({salaries.length} kayıt)</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn btn-primary"
          >
            <Plus size={18} />
            Bordro Ekle
          </button>
          <button
            onClick={handleDownloadPDF}
            className="btn btn-outline"
            disabled={isDownloading || salaries.length === 0}
          >
            <Download size={18} />
            {isDownloading ? 'İndiriliyor...' : 'Toplu PDF'}
          </button>
          <button onClick={() => window.print()} className="btn btn-outline">
            <Printer size={18} />
            Yazdır
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
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">Durum</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">İşlem</th>
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
                        <p className="font-medium text-slate-900">{salary.ad} {salary.soyad}</p>
                        <p className="text-xs text-slate-500">{salary.departman_adi || '-'}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-900">
                    {salary.brut_maas.toLocaleString('tr-TR')} TL
                  </td>
                  <td className="py-4 px-6 text-sm text-emerald-600">
                    +{salary.toplam_ekleme.toLocaleString('tr-TR')} TL
                  </td>
                  <td className="py-4 px-6 text-sm text-red-600">
                    -{salary.toplam_kesinti.toLocaleString('tr-TR')} TL
                  </td>
                  <td className="py-4 px-6 font-bold text-lg text-slate-900">
                    {salary.net_maas.toLocaleString('tr-TR')} TL
                  </td>
                  <td className="py-4 px-6">
                    <span className={`badge ${salary.odendi_mi ? 'badge-success' : 'badge-warning'}`}>
                      {salary.odendi_mi ? 'Ödendi' : 'Bekliyor'}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => handleDownloadSinglePDF(salary.maas_hesap_id, salary.ad, salary.soyad)}
                      className="text-primary-600 hover:text-primary-800 flex items-center gap-1 text-sm"
                      title="Bordro PDF İndir"
                    >
                      <FileText size={16} />
                      PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {salaries.length === 0 && (
          <div className="py-12 text-center">
            <Wallet className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 text-slate-500">Kayıtlı maaş bordrosu bulunamadı</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn btn-primary mt-4"
            >
              <Plus size={18} />
              İlk Bordroyu Oluştur
            </button>
          </div>
        )}
      </div>

      <AddSalaryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => refetch()}
      />
    </div>
  )
}