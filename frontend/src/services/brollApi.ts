import api from './api'

export interface BRollCategory {
  ACTION: string
  LANDSCAPE: string
  TECH: string
  PEOPLE: string
  BUSINESS: string
  LIFESTYLE: string
  TRANSPORT: string
  NATURE: string
  URBAN: string
  OTHER: string
}

export interface BRollStatus {
  PENDING: string
  PROCESSING: string
  AVAILABLE: string
  ERROR: string
}

export interface BRoll {
  id: number
  filename: string
  original_filename: string
  file_path: string
  file_size: number
  mime_type: string
  duration?: number
  width?: number
  height?: number
  fps?: number
  bitrate?: number
  title: string
  description?: string
  tags?: string[]
  category: string
  status: string
  ai_description?: string
  ai_tags?: string[]
  uploaded_by?: number
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface BRollUploadResponse {
  success: boolean
  message: string
  broll?: BRoll
  upload_id?: string
}

export interface BRollListResponse {
  brolls: BRoll[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface BRollUploadData {
  title: string
  description?: string
  category?: string
  tags?: string
  file: File
}

export interface BRollUpdateData {
  title?: string
  description?: string
  category?: string
  tags?: string[]
  is_public?: boolean
}

export interface BRollFilters {
  page?: number
  per_page?: number
  category?: string
  status?: string
  search?: string
  tags?: string
}

export interface StorageStats {
  user_stats: {
    total_files: number
    video_files: number
    image_files: number
    total_size_bytes: number
    total_size_mb: number
  }
  system_stats: {
    total_files: number
    video_files: number
    image_files: number
    total_size_bytes: number
    total_size_mb: number
    directory_path: string
  }
}

class BRollApi {
  async uploadBRoll(data: BRollUploadData): Promise<BRollUploadResponse> {
    const formData = new FormData()
    formData.append('title', data.title)
    if (data.description) formData.append('description', data.description)
    if (data.category) formData.append('category', data.category)
    if (data.tags) formData.append('tags', data.tags)
    formData.append('file', data.file)

    const response = await api.post('/broll/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async listBRoll(filters: BRollFilters = {}): Promise<BRollListResponse> {
    const params = new URLSearchParams()
    if (filters.page) params.append('page', filters.page.toString())
    if (filters.per_page) params.append('per_page', filters.per_page.toString())
    if (filters.category) params.append('category', filters.category)
    if (filters.status) params.append('status', filters.status)
    if (filters.search) params.append('search', filters.search)
    if (filters.tags) params.append('tags', filters.tags)

    const response = await api.get(`/broll/?${params.toString()}`)
    return response.data
  }

  async getBRoll(id: number): Promise<BRoll> {
    const response = await api.get(`/broll/${id}`)
    return response.data
  }

  async updateBRoll(id: number, data: BRollUpdateData): Promise<BRoll> {
    const response = await api.put(`/broll/${id}`, data)
    return response.data
  }

  async deleteBRoll(id: number, permanent: boolean = false): Promise<{ message: string }> {
    const params = permanent ? '?permanent=true' : ''
    const response = await api.delete(`/broll/${id}${params}`)
    return response.data
  }

  async getStorageStats(): Promise<StorageStats> {
    const response = await api.get('/broll/stats/storage')
    return response.data
  }

  getFileUrl(filename: string): string {
    return `/api/broll/files/${filename}`
  }
}

export const brollApi = new BRollApi()