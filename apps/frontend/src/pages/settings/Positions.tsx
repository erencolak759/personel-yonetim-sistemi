import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Trash2, X, Briefcase } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../lib/api';
import { Position, Department } from '../../types';

export default function Positions() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPosition, setEditingPosition] = useState<Position | null>(null);
  const [formData, setFormData] = useState({
    ad: '',
    departman_id: '',
    min_maas: '',
    max_maas: ''
  });

  const { data: positions = [], isLoading } = useQuery<Position[]>({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await api.get('/settings/positions');
      return response.data;
    }
  });

  const { data: departments = [] } = useQuery<Department[]>({
    queryKey: ['departments'],
    queryFn: async () => {
      const response = await api.get('/settings/departments');
      return response.data;
    }
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.post('/settings/positions', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      toast.success('Pozisyon başarıyla eklendi');
      closeModal();
    },
    onError: () => {
      toast.error('Pozisyon eklenirken hata oluştu');
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof formData }) =>
      api.put(`/settings/positions/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      toast.success('Pozisyon başarıyla güncellendi');
      closeModal();
    },
    onError: () => {
      toast.error('Pozisyon güncellenirken hata oluştu');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/settings/positions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      toast.success('Pozisyon başarıyla silindi');
    },
    onError: () => {
      toast.error('Pozisyon silinirken hata oluştu');
    }
  });

  const openModal = (position?: Position) => {
    if (position) {
      setEditingPosition(position);
      setFormData({
        ad: position.ad,
        departman_id: position.departman_id?.toString() || '',
        min_maas: position.min_maas?.toString() || '',
        max_maas: position.max_maas?.toString() || ''
      });
    } else {
      setEditingPosition(null);
      setFormData({ ad: '', departman_id: '', min_maas: '', max_maas: '' });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingPosition(null);
    setFormData({ ad: '', departman_id: '', min_maas: '', max_maas: '' });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingPosition) {
      updateMutation.mutate({ id: editingPosition.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Bu pozisyonu silmek istediğinizden emin misiniz?')) {
      deleteMutation.mutate(id);
    }
  };

  const getDepartmentName = (departmanId?: number) => {
    if (!departmanId) return '-';
    const dept = departments.find(d => d.id === departmanId);
    return dept?.ad || '-';
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '-';
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Briefcase className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-semibold text-gray-800">Pozisyon Yönetimi</h2>
        </div>
        <button
          onClick={() => openModal()}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Yeni Pozisyon
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pozisyon Adı
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Departman
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Min. Maaş
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Max. Maaş
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                İşlemler
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {positions.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  Henüz pozisyon eklenmemiş
                </td>
              </tr>
            ) : (
              positions.map((position) => (
                <tr key={position.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
                        <Briefcase className="w-4 h-4 text-purple-600" />
                      </div>
                      <span className="font-medium text-gray-900">{position.ad}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {getDepartmentName(position.departman_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {formatCurrency(position.min_maas)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {formatCurrency(position.max_maas)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openModal(position)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Düzenle"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(position.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Sil"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-800">
                {editingPosition ? 'Pozisyon Düzenle' : 'Yeni Pozisyon'}
              </h3>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pozisyon Adı
                </label>
                <input
                  type="text"
                  value={formData.ad}
                  onChange={(e) => setFormData({ ...formData, ad: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Pozisyon adını girin"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Departman
                </label>
                <select
                  value={formData.departman_id}
                  onChange={(e) => setFormData({ ...formData, departman_id: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">Departman Seçin</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.ad}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min. Maaş (₺)
                  </label>
                  <input
                    type="number"
                    value={formData.min_maas}
                    onChange={(e) => setFormData({ ...formData, min_maas: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="0"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max. Maaş (₺)
                  </label>
                  <input
                    type="number"
                    value={formData.max_maas}
                    onChange={(e) => setFormData({ ...formData, max_maas: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="0"
                    min="0"
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Kaydediliyor...'
                    : editingPosition
                    ? 'Güncelle'
                    : 'Ekle'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
