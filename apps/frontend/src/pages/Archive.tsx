import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import { Archive as ArchiveIcon, Users, Calendar, Umbrella, Wallet, RotateCcw, Trash2, ChevronDown, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'

interface ArchivedEmployee {
  personel_id: number
  ad: string
  soyad: string
  tc_kimlik_no: string
  departman_adi: string | null
  pozisyon_adi: string | null
  email: string | null
}

export default function Archive() {
  const queryClient = useQueryClient()
  const [expandedEmployee, setExpandedEmployee] = useState<number | null>(null)
  const [detailTab, setDetailTab] = useState<'attendance' | 'leaves' | 'salary'>('attendance')
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)
  const employeesQuery = useQuery({
    queryKey: ['archived-employees'],
    queryFn: async () => {
      const res = await api.get('/employees?archived=1')
      return res.data as ArchivedEmployee[]
    }
  })

  const restoreMutation = useMutation({
    mutationFn: (personelId: number) => api.post(`/employees/${personelId}/restore`),
    onSuccess: () => {
      toast.success('Personel başarıyla geri yüklendi')
      queryClient.invalidateQueries({ queryKey: ['archived-employees'] })
      queryClient.invalidateQueries({ queryKey: ['employees'] })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Geri yükleme hatası')
    }
  })

  const permanentDeleteMutation = useMutation({
    mutationFn: (personelId: number) => api.delete(`/employees/${personelId}/permanent`),
    onSuccess: () => {
      toast.success('Personel ve tüm kayıtları kalıcı olarak silindi')
      queryClient.invalidateQueries({ queryKey: ['archived-employees'] })
      setDeleteConfirm(null)
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Silme hatası')
    }
  })

  const handleExpand = (personelId: number) => {
    if (expandedEmployee === personelId) {
      setExpandedEmployee(null)
    } else {
      setExpandedEmployee(personelId)
      setDetailTab('attendance')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-100 rounded-lg">
            <ArchiveIcon className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Arşiv</h1>
            <p className="text-sm text-slate-500">Arşivlenmiş personeller ve kayıtları</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Users size={16} />
          <span>{employeesQuery.data?.length || 0} arşivlenmiş personel</span>
        </div>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        {employeesQuery.isLoading ? (
          <div className="p-8 text-center text-slate-500">Yükleniyor...</div>
        ) : employeesQuery.data?.length === 0 ? (
          <div className="p-12 text-center">
            <ArchiveIcon className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">Arşivde personel bulunmuyor</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {employeesQuery.data?.map((emp) => (
              <div key={emp.personel_id} className="group">
                <div 
                  className="flex items-center justify-between p-4 hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => handleExpand(emp.personel_id)}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center text-slate-600 font-medium">
                      {emp.ad.charAt(0)}{emp.soyad.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-slate-800">{emp.ad} {emp.soyad}</p>
                      <p className="text-sm text-slate-500">
                        {emp.departman_adi || 'Departman yok'} • {emp.pozisyon_adi || 'Pozisyon yok'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        restoreMutation.mutate(emp.personel_id)
                      }}
                      className="btn btn-sm bg-green-50 text-green-600 hover:bg-green-100 border-green-200"
                      disabled={restoreMutation.isPending}
                    >
                      <RotateCcw size={14} />
                      Geri Yükle
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setDeleteConfirm(emp.personel_id)
                      }}
                      className="btn btn-sm bg-red-50 text-red-600 hover:bg-red-100 border-red-200"
                    >
                      <Trash2 size={14} />
                      Kalıcı Sil
                    </button>
                    {expandedEmployee === emp.personel_id ? (
                      <ChevronUp size={20} className="text-slate-400" />
                    ) : (
                      <ChevronDown size={20} className="text-slate-400" />
                    )}
                  </div>
                </div>
                {expandedEmployee === emp.personel_id && (
                  <EmployeeDetails 
                    personelId={emp.personel_id} 
                    tab={detailTab} 
                    setTab={setDetailTab} 
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      {deleteConfirm !== null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Kalıcı Silme Onayı</h3>
            </div>
            <p className="text-slate-600 mb-6">
              Bu personeli ve tüm kayıtlarını (yoklama, izin, maaş) kalıcı olarak silmek istediğinize emin misiniz? 
              <strong className="text-red-600"> Bu işlem geri alınamaz!</strong>
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="btn btn-outline"
              >
                İptal
              </button>
              <button
                onClick={() => permanentDeleteMutation.mutate(deleteConfirm)}
                className="btn bg-red-600 text-white hover:bg-red-700"
                disabled={permanentDeleteMutation.isPending}
              >
                {permanentDeleteMutation.isPending ? 'Siliniyor...' : 'Kalıcı Olarak Sil'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function EmployeeDetails({ 
  personelId, 
  tab, 
  setTab 
}: { 
  personelId: number
  tab: 'attendance' | 'leaves' | 'salary'
  setTab: (tab: 'attendance' | 'leaves' | 'salary') => void 
}) {
  const attendanceQuery = useQuery({
    queryKey: ['archive-attendance', personelId],
    queryFn: async () => {
      const res = await api.get(`/employees/${personelId}/attendance`)
      return res.data
    },
    enabled: tab === 'attendance'
  })

  const leavesQuery = useQuery({
    queryKey: ['archive-leaves', personelId],
    queryFn: async () => {
      const res = await api.get(`/employees/${personelId}/leaves`)
      return res.data
    },
    enabled: tab === 'leaves'
  })

  const salaryQuery = useQuery({
    queryKey: ['archive-salary', personelId],
    queryFn: async () => {
      const res = await api.get(`/employees/${personelId}/salary`)
      return res.data
    },
    enabled: tab === 'salary'
  })

  return (
    <div className="bg-slate-50 border-t border-slate-200 p-4">
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setTab('attendance')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'attendance' 
              ? 'bg-primary-600 text-white' 
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Calendar size={16} />
          Yoklama
        </button>
        <button
          onClick={() => setTab('leaves')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'leaves' 
              ? 'bg-primary-600 text-white' 
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Umbrella size={16} />
          İzinler
        </button>
        <button
          onClick={() => setTab('salary')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'salary' 
              ? 'bg-primary-600 text-white' 
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Wallet size={16} />
          Bordro
        </button>
      </div>
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {tab === 'attendance' && (
          <>
            {attendanceQuery.isLoading ? (
              <div className="p-4 text-center text-slate-500">Yükleniyor...</div>
            ) : attendanceQuery.data?.length === 0 ? (
              <div className="p-8 text-center text-slate-500">Yoklama kaydı bulunamadı</div>
            ) : (
              <table className="w-full">
                <thead className="bg-slate-50 text-left text-sm text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Tarih</th>
                    <th className="px-4 py-3 font-medium">Durum</th>
                    <th className="px-4 py-3 font-medium">Ek Mesai</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {attendanceQuery.data?.slice(0, 10).map((a: any, idx: number) => (
                    <tr key={idx} className="text-sm">
                      <td className="px-4 py-3 text-slate-800">{a.tarih}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          a.durum === 'Normal' ? 'bg-green-100 text-green-700' :
                          a.durum === 'Izinli' ? 'bg-blue-100 text-blue-700' :
                          a.durum === 'Devamsiz' ? 'bg-red-100 text-red-700' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {a.durum}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{a.ek_mesai_saat || 0} saat</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {attendanceQuery.data?.length > 10 && (
              <div className="p-3 bg-slate-50 text-center text-sm text-slate-500">
                +{attendanceQuery.data.length - 10} kayıt daha
              </div>
            )}
          </>
        )}

        {tab === 'leaves' && (
          <>
            {leavesQuery.isLoading ? (
              <div className="p-4 text-center text-slate-500">Yükleniyor...</div>
            ) : leavesQuery.data?.length === 0 ? (
              <div className="p-8 text-center text-slate-500">İzin kaydı bulunamadı</div>
            ) : (
              <table className="w-full">
                <thead className="bg-slate-50 text-left text-sm text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">İzin Türü</th>
                    <th className="px-4 py-3 font-medium">Başlangıç</th>
                    <th className="px-4 py-3 font-medium">Bitiş</th>
                    <th className="px-4 py-3 font-medium">Gün</th>
                    <th className="px-4 py-3 font-medium">Durum</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {leavesQuery.data?.map((l: any) => (
                    <tr key={l.izin_kayit_id} className="text-sm">
                      <td className="px-4 py-3 text-slate-800">{l.izin_adi}</td>
                      <td className="px-4 py-3 text-slate-600">{l.baslangic_tarihi}</td>
                      <td className="px-4 py-3 text-slate-600">{l.bitis_tarihi}</td>
                      <td className="px-4 py-3 text-slate-600">{l.gun_sayisi}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          l.onay_durumu === 'Onaylandi' ? 'bg-green-100 text-green-700' :
                          l.onay_durumu === 'Reddedildi' ? 'bg-red-100 text-red-700' :
                          'bg-amber-100 text-amber-700'
                        }`}>
                          {l.onay_durumu}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}

        {tab === 'salary' && (
          <>
            {salaryQuery.isLoading ? (
              <div className="p-4 text-center text-slate-500">Yükleniyor...</div>
            ) : salaryQuery.data?.length === 0 ? (
              <div className="p-8 text-center text-slate-500">Maaş kaydı bulunamadı</div>
            ) : (
              <table className="w-full">
                <thead className="bg-slate-50 text-left text-sm text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Dönem</th>
                    <th className="px-4 py-3 font-medium">Brüt</th>
                    <th className="px-4 py-3 font-medium">Kesinti</th>
                    <th className="px-4 py-3 font-medium">Net</th>
                    <th className="px-4 py-3 font-medium">Durum</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {salaryQuery.data?.map((s: any) => (
                    <tr key={s.maas_hesap_id} className="text-sm">
                      <td className="px-4 py-3 text-slate-800">{s.donem_ay}/{s.donem_yil}</td>
                      <td className="px-4 py-3 text-slate-600">{Number(s.brut_maas).toLocaleString('tr-TR')} ₺</td>
                      <td className="px-4 py-3 text-red-600">-{Number(s.toplam_kesinti).toLocaleString('tr-TR')} ₺</td>
                      <td className="px-4 py-3 text-green-600 font-medium">{Number(s.net_maas).toLocaleString('tr-TR')} ₺</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          s.odendi_mi ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {s.odendi_mi ? 'Ödendi' : 'Bekliyor'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  )
}
