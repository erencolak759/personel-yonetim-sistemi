import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Eye,
  FileDown,
  Users,
  X,
} from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'
import type { Employee, Department, Position } from '../types'
import { Avatar, SkeletonTable } from '../components/ui'

export default function Employees() {
  const queryClient = useQueryClient()
  const [archivedView, setArchivedView] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [editModal, setEditModal] = useState<Employee | null>(null)
  const [modalLoading, setModalLoading] = useState(false)
  const [deleteModal, setDeleteModal] = useState<Employee | null>(null)
  const [selectedPozisyonId, setSelectedPozisyonId] = useState<string>('')
  const [selectedKidem, setSelectedKidem] = useState<number>(3)
  const [manualSalary, setManualSalary] = useState<string>('')

  const downloadEmployeeListPdf = async () => {
    try {
      const res = await api.get(`/employees/report?archived=${archivedView ? 1 : 0}`, { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'personel_listesi.pdf'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'PDF indirilemedi')
    }
  }

  const { data, isLoading } = useQuery<{
    personeller: Employee[]
    departmanlar: Department[]
    pozisyonlar: Position[]
  }>({
    queryKey: ['employees', archivedView],
    queryFn: async () => {
      const response = await api.get(`/employees?archived=${archivedView ? 1 : 0}`)
      return { personeller: response.data, departmanlar: [], pozisyonlar: [] }
    },
  })

  const { data: formData } = useQuery<{ departmanlar: Department[]; pozisyonlar: Position[] }>({
    queryKey: ['employee-form-data'],
    queryFn: async () => {
      const response = await api.get('/employees/form-data')
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/employees/${id}`),
    onSuccess: () => {
      toast.success('Personel başarıyla silindi')
      queryClient.invalidateQueries({ queryKey: ['employees', archivedView] })
      setDeleteModal(null)
    },
  })

  const editMutation = useMutation({
    mutationFn: async (personelData: any) => {
      const data = { ...personelData }
      const id = data.personel_id as number
      delete data.personel_id
      const res = await api.put(`/employees/${id}`, data)
      return res
    },
    onSuccess: () => {
      toast.success('Personel bilgileri güncellendi')
      queryClient.invalidateQueries({ queryKey: ['employees', archivedView] })
      setEditModal(null)
    },
  })

  const employees = data?.personeller || []
  const filteredEmployees = employees.filter(
    (emp) =>
      emp.ad.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.soyad.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.tc_kimlik_no.includes(searchQuery) ||
      emp.departman_adi?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Personel Listesi</h1>
            <p className="text-slate-500 mt-1">Yükleniyor...</p>
          </div>
        </div>
        <SkeletonTable rows={8} columns={7} />
      </div>
    )
  }

  return (
    <div className="space-y-6">

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Personel Listesi</h1>
          <p className="text-slate-500 mt-1">
            Toplam {employees.length} kayıtlı çalışan {archivedView ? '(Arşiv)' : ''}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <div className="inline-flex rounded-lg overflow-hidden border bg-white">
            <button onClick={() => setArchivedView(false)} className={`px-3 py-2 text-sm ${!archivedView ? 'bg-primary-600 text-white' : 'text-slate-600'}`}>
              Normal
            </button>
            <button onClick={() => setArchivedView(true)} className={`px-3 py-2 text-sm ${archivedView ? 'bg-amber-500 text-white' : 'text-slate-600'}`}>
              Arşiv
            </button>
          </div>
          <div className="flex gap-2">
            <button onClick={downloadEmployeeListPdf} className="btn btn-outline">
              <FileDown size={18} />
              PDF İndir
            </button>
            <Link to="/admin/employees/add" className="btn btn-primary">
              <Plus size={18} />
              Yeni Personel
            </Link>
          </div>
        </div>
      </div>


      <div className="card p-4">
        <div className="relative">
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            size={20}
          />
          <input
            type="text"
            placeholder="İsim, TC, departman ile arama..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-12"
          />
        </div>
      </div>


      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  TC Kimlik
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Ad Soyad
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Departman
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Pozisyon
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Kıdem
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  Maaş
                </th>
                <th className="text-left py-4 px-6 text-sm font-medium text-slate-600">
                  İletişim
                </th>
                <th className="text-right py-4 px-6 text-sm font-medium text-slate-600">
                  İşlemler
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEmployees.map((employee) => (
                <tr key={employee.personel_id} className="hover:bg-slate-50">
                  <td className="py-4 px-6 text-sm text-slate-500">
                    {employee.tc_kimlik_no}
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <Avatar name={`${employee.ad} ${employee.soyad}`} size="md" />
                      <span className="font-medium text-slate-900">
                        {employee.ad} {employee.soyad}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="badge bg-slate-100 text-slate-700">
                      {employee.departman_adi || '-'}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-600">
                    {employee.pozisyon_adi || '-'}
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-600">
                    {employee.kidem_seviyesi ? `Kıdem ${employee.kidem_seviyesi}` : '-'}
                  </td>
                  <td className="py-4 px-6 text-sm font-medium text-emerald-600">
                    {(employee.taban_maas !== undefined && employee.taban_maas !== null) ? Number(employee.taban_maas).toLocaleString('tr-TR') + ' ₺' : '-'}
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-500">
                    {employee.telefon || '-'}
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        to={`/admin/employees/${employee.personel_id}`}
                        className="p-2 text-slate-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      >
                        <Eye size={18} />
                      </Link>
                      <button
                        onClick={async () => {
                          setModalLoading(true)
                          try {
                            const res = await api.get(`/employees/${employee.personel_id}`)
                            const payload = res.data?.personel ?? res.data
                            setEditModal(payload)
                            setSelectedPozisyonId(String(payload.pozisyon_id ?? ''))
                            setSelectedKidem(Number((payload as any).kidem_seviyesi ?? 3))
                            setManualSalary(
                              (payload as any).ozel_taban_maas != null
                                ? String((payload as any).ozel_taban_maas)
                                : ''
                            )
                          } catch (err: any) {
                            toast.error(err?.response?.data?.error || 'Personel bilgileri alınamadı')
                          } finally {
                            setModalLoading(false)
                          }
                        }}
                        className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => setDeleteModal(employee)}
                        className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredEmployees.length === 0 && (
          <div className="py-12 text-center">
            <Users className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 text-slate-500">
              {searchQuery
                ? 'Arama kriterlerine uygun personel bulunamadı'
                : 'Henüz personel kaydı bulunmuyor'}
            </p>
          </div>
        )}
      </div>


      {editModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900">
                Personel Düzenle
              </h3>
              <button
                onClick={() => setEditModal(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>
            {modalLoading ? (
              <div className="p-6 flex items-center justify-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  const formData = new FormData(e.currentTarget)
                  const personelData: any = Object.fromEntries(formData as any)
                  personelData.personel_id = editModal.personel_id
                  personelData.kidem_seviyesi = selectedKidem
                  personelData.ozel_taban_maas = manualSalary ? Number(manualSalary) : null

                  editMutation.mutate(personelData)
                }}
                className="p-6 space-y-4 overflow-y-auto"
              >
                <div>
                  <label className="label">Ad</label>
                  <input
                    name="ad"
                    defaultValue={editModal.ad}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="label">Soyad</label>
                  <input
                    name="soyad"
                    defaultValue={editModal.soyad}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="label">TC Kimlik No</label>
                  <input
                    name="tc_kimlik_no"
                    defaultValue={editModal.tc_kimlik_no}
                    className="input"
                    maxLength={11}
                    required
                  />
                </div>
                <div>
                  <label className="label">Telefon</label>
                  <input
                    name="telefon"
                    defaultValue={editModal.telefon || ''}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Email</label>
                  <input
                    name="email"
                    type="email"
                    defaultValue={editModal.email || ''}
                    className="input"
                  />
                </div>
                <div className="border-t border-slate-200 pt-4 mt-2">
                  <h4 className="text-sm font-semibold text-slate-900 mb-2">Departman & Maaş</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="label">Departman</label>
                      <select
                        name="departman_id"
                        defaultValue={String((editModal as any).departman_id ?? '')}
                        className="input"
                      >
                        <option value="">Seçiniz...</option>
                        {formData?.departmanlar?.map((d) => (
                          <option key={d.departman_id ?? d.id} value={d.departman_id ?? d.id}>
                            {d.departman_adi ?? d.ad}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="label">Pozisyon</label>
                      <select
                        name="pozisyon_id"
                        className="input"
                        value={selectedPozisyonId}
                        onChange={(e) => setSelectedPozisyonId(e.target.value)}
                      >
                        <option value="">Seçiniz...</option>
                        {formData?.pozisyonlar?.map((p) => (
                          <option key={p.pozisyon_id ?? p.id} value={String(p.pozisyon_id ?? p.id)}>
                            {(p.pozisyon_adi ?? p.ad) || 'Pozisyon'}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="label">Kıdem</label>
                      <div className="grid grid-cols-3 gap-2">
                        {[1, 2, 3].map((k) => (
                          <button
                            key={k}
                            type="button"
                            onClick={() => setSelectedKidem(k)}
                            className={`px-2 py-1 rounded-lg text-xs border ${selectedKidem === k
                              ? 'border-primary-500 bg-primary-50 text-primary-700'
                              : 'border-slate-200 text-slate-600 hover:border-primary-300'
                              }`}
                          >
                            Kıdem {k}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="label">Özel Maaş (opsiyonel)</label>
                      <input
                        type="number"
                        name="ozel_taban_maas"
                        value={manualSalary}
                        onChange={(e) => setManualSalary(e.target.value)}
                        className="input"
                        placeholder="Örneğin 55000"
                      />
                      <p className="mt-1 text-xs text-slate-500">
                        Dolu ise bu tutar kullanılacak, boş bırakılırsa kıdem formülüne göre maaş
                        hesaplanır.
                      </p>
                    </div>
                    <div className="text-xs text-slate-500">
                      <span className="font-medium text-slate-700">Maaş Önizleme: </span>
                      {(() => {
                        const p = formData?.pozisyonlar?.find(
                          (x) => String(x.pozisyon_id ?? x.id) === selectedPozisyonId,
                        )
                        const base = p?.taban_maas ?? 0
                        const diff = (selectedKidem - 1) * 15000
                        const auto = base + diff
                        const effective = manualSalary ? Number(manualSalary) : auto
                        if (!effective) return '-'
                        if (manualSalary) {
                          return `${effective.toLocaleString('tr-TR')} ₺ (Özel maaş)`
                        }
                        return `${effective.toLocaleString('tr-TR')} ₺ (Taban ${base.toLocaleString(
                          'tr-TR',
                        )} ₺ + ${diff.toLocaleString('tr-TR')} ₺)`
                      })()}
                    </div>
                  </div>
                </div>
                <div>
                  <label className="label">Doğum Tarihi</label>
                  <input
                    name="dogum_tarihi"
                    type="date"
                    defaultValue={
                      editModal.dogum_tarihi
                        ? new Date(editModal.dogum_tarihi).toISOString().split('T')[0]
                        : ''
                    }
                    className="input"
                    required
                  />
                </div>
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setEditModal(null)}
                    className="btn btn-secondary flex-1"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={editMutation.isPending}
                    className="btn btn-primary flex-1"
                  >
                    {editMutation.isPending ? 'Kaydediliyor...' : 'Kaydet'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}


      {deleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 className="text-red-600" size={28} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Personeli Sil
              </h3>
              <p className="text-slate-500">
                <strong>{deleteModal.ad} {deleteModal.soyad}</strong> isimli personeli
                silmek istediğinize emin misiniz?
              </p>
            </div>
            <div className="flex gap-3 p-6 border-t border-slate-200">
              <button
                onClick={() => setDeleteModal(null)}
                className="btn btn-secondary flex-1"
              >
                İptal
              </button>
              <button
                onClick={() => deleteMutation.mutate(deleteModal.personel_id)}
                disabled={deleteMutation.isPending}
                className="btn btn-danger flex-1"
              >
                {deleteMutation.isPending ? 'Siliniyor...' : 'Evet, Sil'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
