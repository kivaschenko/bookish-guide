import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('Adding auth header to request:', config.url)
    } else {
      console.log('No token available for request:', config.url)
    }
    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', {
      status: error.response?.status,
      url: error.config?.url,
      data: error.response?.data
    })
    
    if (error.response?.status === 401) {
      console.log('Received 401, clearing token and redirecting to login')
      // Token is invalid, remove it
      localStorage.removeItem('token')
      // Redirect to login page
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api