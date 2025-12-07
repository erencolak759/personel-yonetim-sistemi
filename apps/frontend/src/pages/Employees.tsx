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

export default function Employees() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [editModal, setEditModal] = useState<Employee | null>(null)
  const [deleteModal, setDeleteModal] = useState<Employee | null>(null)

  const { data, isLoading } = useQuery<{
    personeller: Employee[]
    departmanlar: Department[]
    pozisyonlar: Position[]
  }>({
    queryKey: ['employees'],
    queryFn: async () => {
      const response = await api.get('/employees')
      return { personeller: response.data, departmanlar: [], pozisyonlar: [] }
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/employees/${id}`),
    onSuccess: () => {
      toast.success('Personel başarıyla silindi')
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setDeleteModal(null)
    },
  })

  const editMutation = useMutation({
    mutationFn: async (payload: any) => {
      const data = { ...payload.personelData }
      const id = data.personel_id as number
      delete data.personel_id
      const res = await api.put(`/employees/${id}`, data)
      return { res, payload }
    },
    onSuccess: async (result: any) => {
      const { res, payload } = result
      try {
        if (payload?.account && payload.account.username && payload.account.password) {
          await api.post('/users', {
            kullanici_adi: payload.account.username,
            sifre: payload.account.password,
            email: payload.personelData.email || null,
            rol: payload.account.role || 'employee',
            personel_id: payload.personelData.personel_id,
          })
        }

        toast.success('Personel bilgileri güncellendi')
        queryClient.invalidateQueries({ queryKey: ['employees'] })
        setEditModal(null)
      } catch (err: any) {
        toast.error(err?.response?.data?.error || 'Güncelleme sonrası işlem hatası')
      }
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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Personel Listesi</h1>
          <p className="text-slate-500 mt-1">
            Toplam {employees.length} kayıtlı çalışan
          </p>
        </div>
        <div className="flex gap-2">
          <a
            href="#"
            onClick={(e) => { e.preventDefault(); toast('PDF export not available') }}
            className="btn btn-outline text-slate-700"
          >
            <FileDown size={18} />
            PDF İndir
          </a>
          <Link to="/admin/employees/add" className="btn btn-primary">
            <Plus size={18} />
            Yeni Personel
          </Link>
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
                      <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-semibold">
                        {employee.ad[0]}
                      </div>
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
                        onClick={() => setEditModal(employee)}
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
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
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
            <form
              onSubmit={(e) => {
                  e.preventDefault()
                  const formData = new FormData(e.currentTarget)
                  const personelData = Object.fromEntries(formData as any)
                  personelData.personel_id = editModal.personel_id
                  const account = {
                    username: formData.get('kullanici_adi') as string,
                    password: formData.get('sifre') as string,
                    role: (formData.get('rol') as string) || 'employee'
                  }

                  editMutation.mutate({ personelData, account })
                }}
              className="p-6 space-y-4"
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
              <div>
                <label className="label">Kullanıcı Adı (opsiyonel)</label>
                <input name="kullanici_adi" className="input" placeholder="hesap kullanıcı adı" />
              </div>
              <div>
                <label className="label">Şifre (opsiyonel)</label>
                <input name="sifre" type="password" className="input" placeholder="şifre" />
              </div>
              <div>
                <label className="label">Rol</label>
                <select name="rol" className="input">
                  <option value="employee">Employee</option>
                  <option value="admin">Admin</option>
                </select>
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
