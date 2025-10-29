import api from './api'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types/auth'

export const authApi = {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  async register(userData: RegisterRequest): Promise<TokenResponse> {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me')
    return response.data
  },

  async refreshToken(): Promise<TokenResponse> {
    const response = await api.post('/auth/refresh')
    return response.data
  }
}