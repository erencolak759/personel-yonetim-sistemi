import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Building, X } from 'lucide-react'
import api from '../../lib/api'
import toast from 'react-hot-toast'

interface Department {
  departman_id: number
  departman_adi: string
  personel_sayisi: number
}

export default function Departments() {
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [editDept, setEditDept] = useState<Department | null>(null)
  const [deleteDept, setDeleteDept] = useState<Department | null>(null)

  const { data, isLoading } = useQuery<Department[]>({
    queryKey: ['departments'],
    queryFn: async () => {
      const response = await api.get('/settings/departments')
      const rows: any[] = response.data || []
      return rows.map((r) => ({
        departman_id: r.id,
        departman_adi: r.ad,
        personel_sayisi: r.personel_sayisi || 0,
      }))
    },
  })

  const addMutation = useMutation({
    mutationFn: (name: string) =>
      api.post('/settings/departments', { ad: name }),
    onSuccess: () => {
      toast.success('Departman eklendi')
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setShowAddModal(false)
    },
  })

  const editMutation = useMutation({
    mutationFn: (dept: Department) =>
      api.put(`/settings/departments/${dept.departman_id}`, { ad: dept.departman_adi }),
    onSuccess: () => {
      toast.success('Departman güncellendi')
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setEditDept(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      api.delete(`/settings/departments/${id}`),
    onSuccess: () => {
      toast.success('Departman silindi')
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setDeleteDept(null)
    },
  })

  const departments = data || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Departmanlar</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary text-sm"
        >
          <Plus size={16} />
          Yeni Departman
        </button>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                Departman Adı
              </th>
              <th className="text-left py-3 px-6 text-sm font-medium text-slate-600">
                Personel Sayısı
              </th>
              <th className="text-right py-3 px-6 text-sm font-medium text-slate-600">
                İşlemler
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {departments.map((dept) => (
              <tr key={dept.departman_id} className="hover:bg-slate-50">
                <td className="py-3 px-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center">
                      <Building size={16} />
                    </div>
                    <span className="font-medium text-slate-900">
                      {dept.departman_adi}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-6">
                  <span className="badge bg-slate-100 text-slate-700">
                    {dept.personel_sayisi} Kişi
                  </span>
                </td>
                <td className="py-3 px-6">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setEditDept(dept)}
                      className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => setDeleteDept(dept)}
                      className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {departments.length === 0 && (
          <div className="py-12 text-center text-slate-500">
            Henüz departman eklenmemiş
          </div>
        )}
      </div>
      {showAddModal && (
        <Modal
          title="Yeni Departman"
          onClose={() => setShowAddModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              addMutation.mutate(formData.get('departman_adi') as string)
            }}
          >
            <div className="mb-4">
              <label className="label">Departman Adı</label>
              <input name="departman_adi" className="input" required autoFocus />
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="btn btn-secondary flex-1"
              >
                İptal
              </button>
              <button
                type="submit"
                disabled={addMutation.isPending}
                className="btn btn-primary flex-1"
              >
                {addMutation.isPending ? 'Ekleniyor...' : 'Ekle'}
              </button>
            </div>
          </form>
        </Modal>
      )}
      {editDept && (
        <Modal title="Departman Düzenle" onClose={() => setEditDept(null)}>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              editMutation.mutate({
                ...editDept,
                departman_adi: formData.get('departman_adi') as string,
              })
            }}
          >
            <div className="mb-4">
              <label className="label">Departman Adı</label>
              <input
                name="departman_adi"
                className="input"
                defaultValue={editDept.departman_adi}
                required
              />
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setEditDept(null)}
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
        </Modal>
      )}
      {deleteDept && (
        <Modal title="Departman Sil" onClose={() => setDeleteDept(null)}>
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Trash2 className="text-red-600" size={28} />
            </div>
            <p className="text-slate-600">
              <strong>{deleteDept.departman_adi}</strong> departmanını silmek
              istediğinize emin misiniz?
            </p>
            {deleteDept.personel_sayisi > 0 && (
              <p className="text-amber-600 text-sm mt-2">
                Bu departmanda {deleteDept.personel_sayisi} personel bulunuyor!
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setDeleteDept(null)}
              className="btn btn-secondary flex-1"
            >
              İptal
            </button>
            <button
              onClick={() => deleteMutation.mutate(deleteDept.departman_id)}
              disabled={deleteMutation.isPending}
              className="btn btn-danger flex-1"
            >
              {deleteMutation.isPending ? 'Siliniyor...' : 'Evet, Sil'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function Modal({
  title,
  children,
  onClose,
}: {
  title: string
  children: React.ReactNode
  onClose: () => void
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}
