import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Phone,
  Mail,
  Calendar,
  FileText,
  Umbrella,
  Wallet,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import api from '../lib/api'

interface EmployeeDetailData {
  personel: {
    personel_id: number
    tc_kimlik_no: string
    ad: string
    soyad: string
    dogum_tarihi: string
    telefon: string | null
    email: string | null
    ise_giris_tarihi: string
    departman_adi: string | null
    pozisyon_adi: string | null
    taban_maas: number | null
    kidem_seviyesi?: number | null
  }
  devam_ozet: { durum: string; adet: number }[]
  izinler: {
    izin_adi: string
    baslangic_tarihi: string
    bitis_tarihi: string
    gun_sayisi: number
    onay_durumu: string
  }[]
  maaslar: {
    donem_yil: number
    donem_ay: number
    brut_maas: number
    toplam_ekleme: number
    toplam_kesinti: number
    net_maas: number
    odendi_mi: boolean
  }[]
}

export default function EmployeeDetail() {
  const { id } = useParams()

  const downloadEmployeeDetailPdf = async (personelId?: string | undefined) => {
    if (!personelId) return
    try {
      const res = await api.get(`/employees/${personelId}/report`, { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `personel_${personelId}_detay.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF indirilemedi', err)
    }
  }

  const { data, isLoading } = useQuery<EmployeeDetailData>({
    queryKey: ['employee', id],
    queryFn: async () => {
      const response = await api.get(`/employees/${id}`)
      const resp = response.data || {}
      return {
        personel: resp.personel,
        devam_ozet: resp.devam_ozet || [],
        izinler: resp.izinler || [],
        maaslar: resp.maaslar || [],
      }
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Personel bulunamadı</p>
      </div>
    )
  }

  const { personel, devam_ozet, izinler, maaslar } = data

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/admin/employees"
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft size={24} className="text-slate-600" />
        </Link>
        <div className="ml-auto">
          <button onClick={() => downloadEmployeeDetailPdf(id)} className="btn btn-outline">
            <Calendar size={16} /> PDF
          </button>
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {personel.ad} {personel.soyad}
          </h1>
          <p className="text-slate-500">
            {personel.pozisyon_adi || 'Pozisyon Belirtilmemiş'} •{' '}
            {personel.departman_adi || 'Departman Belirtilmemiş'}{' '}
            {personel.kidem_seviyesi ? `• Kıdem ${personel.kidem_seviyesi}` : ''}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <div className="card p-6 text-center">
            <div className="w-24 h-24 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-3xl font-bold mx-auto mb-4">
              {personel.ad[0]}
              {personel.soyad[0]}
            </div>
            <h2 className="text-xl font-semibold text-slate-900">
              {personel.ad} {personel.soyad}
            </h2>
            <p className="text-slate-500">{personel.pozisyon_adi || '-'}</p>

            <div className="mt-6 space-y-3">
              {personel.telefon && (
                <a
                  href={`tel:${personel.telefon}`}
                  className="btn btn-outline w-full justify-start"
                >
                  <Phone size={18} />
                  {personel.telefon}
                </a>
              )}
              {personel.email && (
                <a
                  href={`mailto:${personel.email}`}
                  className="btn btn-outline w-full justify-start"
                >
                  <Mail size={18} />
                  {personel.email}
                </a>
              )}
            </div>
          </div>

          <div className="card">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                <FileText size={18} className="text-primary-600" />
                Kişisel Bilgiler
              </h3>
            </div>
            <div className="p-6 space-y-4">
              <InfoRow label="TC Kimlik No" value={personel.tc_kimlik_no} />
              <InfoRow label="Doğum Tarihi" value={personel.dogum_tarihi || '-'} />
              <InfoRow label="İşe Giriş" value={personel.ise_giris_tarihi} />
              <InfoRow label="Departman" value={personel.departman_adi || '-'} />
              <InfoRow
                label="Kıdem"
                value={personel.kidem_seviyesi ? `Kıdem ${personel.kidem_seviyesi}` : '-'}
              />
              <InfoRow
                label="Maaş"
                value={`${personel.taban_maas?.toLocaleString('tr-TR') || 0} ₺`}
                highlight
              />
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                <Calendar size={18} className="text-amber-500" />
                Devam Durumu (Son 30 Gün)
              </h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-3 gap-4">
                {devam_ozet.map((item) => (
                  <div
                    key={item.durum}
                    className={`p-4 rounded-xl text-center ${
                      item.durum === 'Normal'
                        ? 'bg-emerald-100 text-emerald-700'
                        : item.durum === 'Izinli'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {item.durum === 'Normal' && <CheckCircle className="mx-auto mb-2" size={24} />}
                    {item.durum === 'Izinli' && <Umbrella className="mx-auto mb-2" size={24} />}
                    {item.durum === 'Devamsiz' && <XCircle className="mx-auto mb-2" size={24} />}
                    <div className="text-2xl font-bold">{item.adet}</div>
                    <div className="text-sm">
                      {item.durum === 'Normal' ? 'Var' : item.durum === 'Izinli' ? 'İzinli' : 'Devamsız'}
                    </div>
                  </div>
                ))}
                {devam_ozet.length === 0 && (
                  <p className="col-span-3 text-center text-slate-500 py-4">
                    Son 30 günde devam kaydı bulunmuyor
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                <Umbrella size={18} className="text-cyan-500" />
                İzin Geçmişi
              </h3>
              <span className="badge badge-info">{izinler.length} Kayıt</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      İzin Türü
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Başlangıç
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Bitiş
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Süre
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Durum
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {izinler.map((izin, index) => (
                    <tr key={index}>
                      <td className="py-3 px-6 text-sm">{izin.izin_adi}</td>
                      <td className="py-3 px-6 text-sm text-slate-600">
                        {izin.baslangic_tarihi}
                      </td>
                      <td className="py-3 px-6 text-sm text-slate-600">
                        {izin.bitis_tarihi}
                      </td>
                      <td className="py-3 px-6">
                        <span className="badge bg-slate-100 text-slate-700">
                          {izin.gun_sayisi} Gün
                        </span>
                      </td>
                      <td className="py-3 px-6">
                        <span
                          className={`badge ${
                            izin.onay_durumu === 'Onaylandi'
                              ? 'badge-success'
                              : izin.onay_durumu === 'Reddedildi'
                              ? 'badge-danger'
                              : 'badge-warning'
                          }`}
                        >
                          {izin.onay_durumu === 'Onaylandi'
                            ? 'Onaylandı'
                            : izin.onay_durumu === 'Reddedildi'
                            ? 'Reddedildi'
                            : 'Beklemede'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {izinler.length === 0 && (
                <div className="py-8 text-center text-slate-500">
                  Henüz izin kaydı bulunmuyor
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                <Wallet size={18} className="text-emerald-500" />
                Maaş Bordroları (Son 6 Ay)
              </h3>
              <span className="badge badge-success">{maaslar.length} Kayıt</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Dönem
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Brüt
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Eklemeler
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Kesintiler
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Net
                    </th>
                    <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                      Durum
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {maaslar.map((maas, index) => (
                    <tr key={index}>
                      <td className="py-3 px-6 font-medium text-slate-900">
                        {maas.donem_ay}/{maas.donem_yil}
                      </td>
                      <td className="py-3 px-6 text-sm">
                        {maas.brut_maas.toLocaleString('tr-TR')} ₺
                      </td>
                      <td className="py-3 px-6 text-sm text-emerald-600">
                        +{maas.toplam_ekleme.toLocaleString('tr-TR')} ₺
                      </td>
                      <td className="py-3 px-6 text-sm text-red-600">
                        -{maas.toplam_kesinti.toLocaleString('tr-TR')} ₺
                      </td>
                      <td className="py-3 px-6 font-bold text-slate-900">
                        {maas.net_maas.toLocaleString('tr-TR')} ₺
                      </td>
                      <td className="py-3 px-6">
                        <span
                          className={`badge ${
                            maas.odendi_mi ? 'badge-success' : 'badge-warning'
                          }`}
                        >
                          {maas.odendi_mi ? 'Ödendi' : 'Bekliyor'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {maaslar.length === 0 && (
                <div className="py-8 text-center text-slate-500">
                  Henüz maaş kaydı bulunmuyor
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function InfoRow({
  label,
  value,
  highlight = false,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-slate-500">{label}</span>
      <span
        className={`text-sm ${
          highlight ? 'font-bold text-emerald-600' : 'text-slate-900'
        }`}
      >
        {value}
      </span>
    </div>
  )
}
