import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Building, Briefcase, Tags, CircleUserIcon } from 'lucide-react'
import Departments from './settings/Departments'
import Positions from './settings/Positions'
import LeaveTypes from './settings/LeaveTypes'
import Profile from './settings/Profile'
import ChangePassword from './ChangePassword'

const allSettingsNav = [
  { name: 'Departmanlar', href: 'departments', icon: Building },
  { name: 'Pozisyonlar', href: 'positions', icon: Briefcase },
  { name: 'İzin Türleri', href: 'leave-types', icon: Tags },
  { name: 'Şifre Değiştir', href: 'change-password', icon: CircleUserIcon },
]

export default function Settings() {
  const { user } = useAuth()

    if (!user || user.rol !== 'admin') {
      return (
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Hesap Ayarlarım</h1>
            <p className="text-slate-500 mt-1">Kişisel bilgilerinizi güncelleyin</p>
          </div>

          <div className="space-y-6">
            <Profile />

            <div>
              <h2 className="text-lg font-semibold">Hesap ve Güvenlik</h2>
              <p className="text-sm text-slate-500 mb-3">Şifrenizi buradan değiştirebilirsiniz.</p>
              <ChangePassword />
            </div>
          </div>
        </div>
      )
  }

  const navItems = allSettingsNav

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Ayarlar</h1>
        <p className="text-slate-500 mt-1">Sistem yapılandırmasını yönetin</p>
      </div>

      <div className="flex gap-6">
        <div className="w-64 shrink-0">
          <nav className="card p-2 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-primary-50 text-primary-700' : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                <item.icon size={18} />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex-1">
          <Routes>
            <Route index element={<Navigate to="departments" replace />} />
            <Route path="departments" element={<Departments />} />
            <Route path="positions" element={<Positions />} />
            <Route path="leave-types" element={<LeaveTypes />} />
            <Route path="change-password" element={<ChangePassword />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}
