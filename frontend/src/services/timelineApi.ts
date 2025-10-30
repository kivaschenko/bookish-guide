import api from './api'

// Timeline interfaces matching backend schemas
export interface BrollClip {
  video: string
  start: number
  duration: number
  score: number
}

export interface Rush {
  duration: number
  brolls: BrollClip[]
  message: string
}

export interface TimelineData {
  rushes: Record<string, Rush>
}

export interface TimelineItem {
  start_time: number
  end_time: number
  duration: number
  broll_path: string
  bullet_point: string
  similarity_score?: number
  image?: string
  metadata?: Record<string, any>
}

export interface TimelineUpdateRequest {
  timeline_data: Record<string, any>
}

export interface UploadResponse {
  success: boolean
  message: string
  file_path?: string
  file_size?: number
}

export interface ProjectInfo {
  project_name: string
  temp_path: string
  broll_timing_exists: boolean
  b_roll_path: string
  projects_path: string
}

export interface EffectConfig {
  type: 'fade' | 'zoom' | 'slide' | 'blur' | 'color_correction'
  duration: number
  start_time: number
  parameters?: Record<string, any>
}

export interface OverlayConfig {
  type: 'text' | 'image' | 'logo'
  content: string
  position: { x: number; y: number }
  size: { width: number; height: number }
  start_time: number
  duration: number
  style?: Record<string, any>
}

class TimelineApi {
  async getTimeline(): Promise<TimelineData> {
    const response = await api.get('/timeline')
    return response.data
  }

  async updateTimeline(timelineData: Record<string, any>): Promise<{ success: string; message: string }> {
    const response = await api.post('/timeline', { timeline_data: timelineData })
    return response.data
  }

  async uploadOverlayImage(file: File, brollIndex: number): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('broll_index', brollIndex.toString())

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async deleteUploadedFile(filename: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/upload/${filename}`)
    return response.data
  }

  async getProjectInfo(): Promise<ProjectInfo> {
    const response = await api.get('/project-info')
    return response.data
  }

  async getSystemStatus(): Promise<any> {
    const response = await api.get('/status')
    return response.data
  }

  // Helper method to generate preview URL
  getPreviewUrl(projectId: number): string {
    return `/api/projects/${projectId}/preview`
  }

  // Helper method to get B-roll file URL
  getBrollFileUrl(filename: string): string {
    return `/api/broll/files/${filename}`
  }
}

export const timelineApi = new TimelineApi()