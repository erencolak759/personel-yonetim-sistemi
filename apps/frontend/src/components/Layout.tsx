import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard,
  Users,
  Calendar,
  Umbrella,
  Wallet,
  Settings,
  LogOut,
  Menu,
  X,
  Archive,
} from 'lucide-react'
import { useState } from 'react'

const adminNavigation = [
  { name: 'Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { name: 'Personel', href: '/admin/employees', icon: Users },
  { name: 'Yoklama', href: '/admin/attendance', icon: Calendar },
  { name: 'İzinler', href: '/admin/leaves', icon: Umbrella },
  { name: 'Maaşlar', href: '/admin/salary', icon: Wallet },
  { name: 'Arşiv', href: '/admin/archive', icon: Archive },
  { name: 'Ayarlar', href: '/admin/settings', icon: Settings },
]

const userNavigation = [
  { name: 'İzinler', href: '/user/leaves', icon: Umbrella },
  { name: 'Ayarlar', href: '/user/settings', icon: Settings },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">HR</span>
            </div>
            <span className="font-semibold text-slate-900">Portal</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-500 hover:text-slate-700"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {(() => {
            const navToShow = user?.rol === 'admin' ? adminNavigation : userNavigation
            return navToShow.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }: { isActive: boolean }) =>
                  `sidebar-link ${isActive ? 'active' : ''}`
                }
              >
                <item.icon size={20} />
                {item.name}
              </NavLink>
            ))
          })()}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center font-semibold">
              {user?.kullanici_adi?.substring(0, 2).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {user?.kullanici_adi}
              </p>
              <p className="text-xs text-slate-500 capitalize">{user?.rol}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full btn btn-secondary text-sm"
          >
            <LogOut size={16} />
            Çıkış Yap
          </button>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-slate-500 hover:text-slate-700"
            >
              <Menu size={24} />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-4" />
          </div>
        </header>
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
