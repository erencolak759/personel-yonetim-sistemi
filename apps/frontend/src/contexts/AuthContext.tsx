import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from '../lib/api'
import type { User } from '../types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<User | null>
  refresh: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await api.get('/auth/me')
      if (response.data.authenticated && response.data.user) {
        setUser(response.data.user)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string): Promise<User | null> => {
    try {
      const response = await api.post('/auth/login', { username, password })
      const { token, user } = response.data

      if (token && user) {
        localStorage.setItem('authToken', token)
        setUser(user)
        return user
      }
      return null
    } catch {
      return null
    }
  }

  const refresh = async () => {
    try {
      const response = await api.get('/auth/me')
      if (response.data.authenticated && response.data.user) {
        setUser(response.data.user)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      localStorage.removeItem('authToken')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        refresh,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
