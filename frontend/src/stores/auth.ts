import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, RegisterRequest, TokenResponse } from '@/types/auth'
import { authApi } from '@/services/authApi'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value && !!token.value)

  // Actions
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = null
    localStorage.removeItem('token')
  }

  const setUser = (newUser: User) => {
    user.value = newUser
  }

  const clearUser = () => {
    user.value = null
  }

  const setError = (message: string) => {
    error.value = message
  }

  const clearError = () => {
    error.value = null
  }

  const login = async (credentials: LoginRequest): Promise<boolean> => {
    try {
      isLoading.value = true
      clearError()

      const response = await authApi.login(credentials)
      
      setToken(response.access_token)
      setUser(response.user)
      
      return true
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
      return false
    } finally {
      isLoading.value = false
    }
  }

  const register = async (userData: RegisterRequest): Promise<boolean> => {
    try {
      isLoading.value = true
      clearError()

      const response = await authApi.register(userData)
      
      setToken(response.access_token)
      setUser(response.user)
      
      return true
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      clearToken()
      clearUser()
      clearError()
    }
  }

  const checkAuth = async () => {
    if (!token.value) {
      return
    }

    try {
      const user = await authApi.getCurrentUser()
      setUser(user)
    } catch (err) {
      // Token is invalid, clear it
      clearToken()
      clearUser()
    }
  }

  const refreshToken = async (): Promise<boolean> => {
    try {
      const response = await authApi.refreshToken()
      setToken(response.access_token)
      setUser(response.user)
      return true
    } catch (err) {
      clearToken()
      clearUser()
      return false
    }
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    
    // Actions
    login,
    register,
    logout,
    checkAuth,
    refreshToken,
    setError,
    clearError
  }
})