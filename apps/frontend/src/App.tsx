import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import EmployeeDetail from './pages/EmployeeDetail'
import AddEmployee from './pages/AddEmployee'
import Attendance from './pages/Attendance'
import Leaves from './pages/Leaves'
import Salary from './pages/Salary'
import Announcements from './pages/Announcements'
import Candidates from './pages/Candidates'
import Settings from './pages/Settings'
import ChangePassword from './pages/ChangePassword'
import UserHome from './pages/UserDashboard'
import UserPayroll from './pages/UserPayroll'
import Apply from './pages/Apply'
import Users from './pages/Users'
import Archive from './pages/Archive'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) return <Navigate to="/login" />

  if (user?.ilk_giris && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }

  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" />
  if (user?.rol !== 'admin') return <Navigate to="/user/leaves" />
  return <>{children}</>
}

function UserRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" />
  if (user?.rol === 'admin') return <Navigate to="/admin/dashboard" />
  return <>{children}</>
}

function RoleRedirect() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" />
  return user.rol === 'admin' ? <Navigate to="/admin/dashboard" replace /> : <Navigate to="/user/dashboard" replace />
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/apply" element={<Apply />} />
        <Route
          path="/admin"
          element={
            <PrivateRoute>
              <AdminRoute>
                <Layout />
              </AdminRoute>
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="employees" element={<Employees />} />
          <Route path="employees/add" element={<AddEmployee />} />
          <Route path="employees/:id" element={<EmployeeDetail />} />
          <Route path="users" element={<Users />} />
          <Route path="archive" element={<Archive />} />
          <Route path="attendance" element={<Attendance />} />
          <Route path="leaves" element={<Leaves />} />
          <Route path="salary" element={<Salary />} />
          <Route path="announcements" element={<Announcements />} />
          <Route path="candidates" element={<Candidates />} />
          <Route path="settings/*" element={<Settings />} />
        </Route>

        <Route
          path="/user"
          element={
            <PrivateRoute>
              <UserRoute>
                <Layout />
              </UserRoute>
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/user/dashboard" replace />} />
          <Route path="dashboard" element={<UserHome />} />
          <Route path="payroll" element={<UserPayroll />} />
          <Route path="leaves" element={<Leaves />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route path="/" element={<RoleRedirect />} />

        {/* change-password should render without the main Layout/sidebar */}
        <Route
          path="/change-password"
          element={
            <PrivateRoute>
              <ChangePassword />
            </PrivateRoute>
          }
        />
      </Routes>
    </AuthProvider>
  )
}

export default App
