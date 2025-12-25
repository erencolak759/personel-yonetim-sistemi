import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import {
    LayoutDashboard,
    Users,
    Calendar,
    Umbrella,
    Wallet,
    Megaphone,
    UserPlus,
    Settings,
    LogOut,
    Menu,
    X,
    Shield,
    ChevronDown,
    Search,
    Bell,
    Plus,
    LucideIcon,
} from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import Avatar from '../ui/Avatar'
import Button from '../ui/Button'

interface NavItem {
    name: string
    href?: string
    icon: LucideIcon
    children?: { name: string; href: string }[]
}

const adminNavigation: NavItem[] = [
    { name: 'Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
    {
        name: 'Personel',
        icon: Users,
        children: [
            { name: 'Personel Listesi', href: '/admin/employees' },
            { name: 'Yeni Personel', href: '/admin/employees/add' },
            { name: 'Arşiv', href: '/admin/archive' },
        ],
    },
    { name: 'Kullanıcılar', href: '/admin/users', icon: Shield },
    { name: 'Yoklama', href: '/admin/attendance', icon: Calendar },
    { name: 'İzinler', href: '/admin/leaves', icon: Umbrella },
    { name: 'Maaşlar', href: '/admin/salary', icon: Wallet },
    { name: 'Adaylar', href: '/admin/candidates', icon: UserPlus },
    { name: 'Duyurular', href: '/admin/announcements', icon: Megaphone },
    { name: 'Ayarlar', href: '/admin/settings', icon: Settings },
]

const userNavigation: NavItem[] = [
    { name: 'Ana Sayfa', href: '/user/dashboard', icon: LayoutDashboard },
    { name: 'Bordro', href: '/user/payroll', icon: Wallet },
    { name: 'İzinler', href: '/user/leaves', icon: Umbrella },
    { name: 'Ayarlar', href: '/user/settings', icon: Settings },
]

function NavItemComponent({ item, closeSidebar }: { item: NavItem; closeSidebar: () => void }) {
    const location = useLocation()
    const [isOpen, setIsOpen] = useState(false)
    const hasChildren = item.children && item.children.length > 0

    // Check if any child is active
    const isChildActive = hasChildren && item.children?.some(child =>
        location.pathname.startsWith(child.href)
    )

    // Auto-expand if child is active
    useEffect(() => {
        if (isChildActive) {
            setIsOpen(true)
        }
    }, [isChildActive])

    if (hasChildren) {
        return (
            <div>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={`w-full sidebar-link justify-between ${isChildActive ? 'text-primary-700' : ''}`}
                >
                    <span className="flex items-center gap-3">
                        <item.icon size={20} />
                        {item.name}
                    </span>
                    <ChevronDown
                        size={16}
                        className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                    />
                </button>
                {isOpen && (
                    <div className="ml-9 mt-1 space-y-1">
                        {item.children?.map((child) => (
                            <NavLink
                                key={child.href}
                                to={child.href}
                                onClick={closeSidebar}
                                className={({ isActive }) =>
                                    `block px-3 py-2 text-sm rounded-md transition-colors ${isActive
                                        ? 'text-primary-700 bg-primary-50 font-medium'
                                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                                    }`
                                }
                            >
                                {child.name}
                            </NavLink>
                        ))}
                    </div>
                )}
            </div>
        )
    }

    return (
        <NavLink
            to={item.href!}
            onClick={closeSidebar}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
            <item.icon size={20} />
            {item.name}
        </NavLink>
    )
}

export default function Layout() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [userMenuOpen, setUserMenuOpen] = useState(false)
    const [quickActionsOpen, setQuickActionsOpen] = useState(false)
    const userMenuRef = useRef<HTMLDivElement>(null)
    const quickActionsRef = useRef<HTMLDivElement>(null)

    const handleLogout = async () => {
        await logout()
        navigate('/login')
    }

    const closeSidebar = () => setSidebarOpen(false)

    // Close dropdowns when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
                setUserMenuOpen(false)
            }
            if (quickActionsRef.current && !quickActionsRef.current.contains(event.target as Node)) {
                setQuickActionsOpen(false)
            }
        }

        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const navItems = user?.rol === 'admin' ? adminNavigation : userNavigation
    const isAdmin = user?.rol === 'admin'

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                    onClick={closeSidebar}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`fixed top-0 left-0 z-50 h-full w-[260px] bg-white border-r border-slate-200 
                   transform transition-transform duration-200 ease-in-out lg:translate-x-0 
                   flex flex-col ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
            >
                {/* Logo */}
                <div className="flex items-center justify-between h-16 px-6 border-b border-slate-200 shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-sm">
                            <span className="text-white font-bold text-sm">HR</span>
                        </div>
                        <div>
                            <span className="font-semibold text-slate-900 text-sm">HR Portal</span>
                            <span className="block text-[10px] text-slate-400 font-medium uppercase tracking-wider">
                                {isAdmin ? 'Admin' : 'Kullanıcı'}
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={closeSidebar}
                        className="lg:hidden p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 overflow-y-auto py-4 px-3">
                    <div className="space-y-1">
                        {navItems.map((item) => (
                            <NavItemComponent
                                key={item.name}
                                item={item}
                                closeSidebar={closeSidebar}
                            />
                        ))}
                    </div>
                </nav>

                {/* User section */}
                <div className="p-4 border-t border-slate-200 shrink-0">
                    <div className="flex items-center gap-3 mb-3">
                        <Avatar name={user?.kullanici_adi || 'User'} size="md" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-900 truncate">
                                {user?.kullanici_adi}
                            </p>
                            <p className="text-xs text-slate-500 capitalize">{user?.rol}</p>
                        </div>
                    </div>
                    <Button
                        variant="secondary"
                        leftIcon={LogOut}
                        onClick={handleLogout}
                        className="w-full justify-center"
                        size="sm"
                    >
                        Çıkış Yap
                    </Button>
                </div>
            </aside>

            {/* Main content area */}
            <div className="lg:pl-[260px]">
                {/* Top bar */}
                <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200/80">
                    <div className="flex items-center justify-between h-16 px-4 sm:px-6">
                        {/* Left side */}
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setSidebarOpen(true)}
                                className="lg:hidden p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                <Menu size={22} />
                            </button>

                            {/* Search (desktop only) */}
                            <div className="hidden md:block relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Ara... (⌘K)"
                                    className="w-64 h-9 pl-10 pr-4 text-sm bg-slate-100 border-0 rounded-lg 
                           placeholder:text-slate-400 focus:bg-white focus:ring-2 focus:ring-primary-500/20 
                           focus:outline-none transition-all"
                                />
                            </div>
                        </div>

                        {/* Right side */}
                        <div className="flex items-center gap-2">
                            {/* Quick Actions (Admin only) */}
                            {isAdmin && (
                                <div className="relative" ref={quickActionsRef}>
                                    <button
                                        onClick={() => setQuickActionsOpen(!quickActionsOpen)}
                                        className="flex items-center gap-1.5 h-9 px-3 text-sm font-medium text-slate-700 
                             bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                                    >
                                        <Plus size={16} />
                                        <span className="hidden sm:inline">Yeni</span>
                                    </button>
                                    {quickActionsOpen && (
                                        <div className="dropdown-menu right-0 w-48 animate-fade-in">
                                            <button
                                                onClick={() => {
                                                    navigate('/admin/employees/add')
                                                    setQuickActionsOpen(false)
                                                }}
                                                className="dropdown-item w-full text-left"
                                            >
                                                <UserPlus size={16} />
                                                Yeni Personel
                                            </button>
                                            <button
                                                onClick={() => {
                                                    navigate('/admin/announcements')
                                                    setQuickActionsOpen(false)
                                                }}
                                                className="dropdown-item w-full text-left"
                                            >
                                                <Megaphone size={16} />
                                                Yeni Duyuru
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Notifications (placeholder) */}
                            <button className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors">
                                <Bell size={20} />
                                {/* Notification dot */}
                                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-error-500 rounded-full" />
                            </button>

                            {/* User menu */}
                            <div className="relative hidden sm:block" ref={userMenuRef}>
                                <button
                                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                                    className="flex items-center gap-2 p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
                                >
                                    <Avatar name={user?.kullanici_adi || 'User'} size="sm" />
                                    <ChevronDown
                                        size={16}
                                        className={`text-slate-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`}
                                    />
                                </button>
                                {userMenuOpen && (
                                    <div className="dropdown-menu right-0 w-56 animate-fade-in">
                                        <div className="px-4 py-3 border-b border-slate-100">
                                            <p className="text-sm font-medium text-slate-900">{user?.kullanici_adi}</p>
                                            <p className="text-xs text-slate-500">{user?.email || 'Kullanıcı'}</p>
                                        </div>
                                        <div className="py-1">
                                            <button
                                                onClick={() => {
                                                    navigate(isAdmin ? '/admin/settings' : '/user/settings')
                                                    setUserMenuOpen(false)
                                                }}
                                                className="dropdown-item w-full text-left"
                                            >
                                                <Settings size={16} />
                                                Ayarlar
                                            </button>
                                            <button
                                                onClick={handleLogout}
                                                className="dropdown-item danger w-full text-left"
                                            >
                                                <LogOut size={16} />
                                                Çıkış Yap
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </header>

                {/* Page content */}
                <main className="p-4 sm:p-6 lg:p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
