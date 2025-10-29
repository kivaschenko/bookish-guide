import api from './api'
import type { 
  Project, 
  ProjectCreate, 
  ProjectUpdate, 
  ProjectListResponse,
  VideoGeneration,
  VideoGenerationCreate
} from '@/types/project'

export const projectApi = {
  async getProjects(params?: { skip?: number; limit?: number; status_filter?: string }): Promise<ProjectListResponse> {
    const response = await api.get('/projects', { params })
    return response.data
  },

  async getProject(id: number): Promise<Project> {
    const response = await api.get(`/projects/${id}`)
    return response.data
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await api.post('/projects', data)
    return response.data
  },

  async updateProject(id: number, data: ProjectUpdate): Promise<Project> {
    const response = await api.put(`/projects/${id}`, data)
    return response.data
  },

  async deleteProject(id: number): Promise<void> {
    await api.delete(`/projects/${id}`)
  },

  async getVideoGenerations(projectId: number): Promise<VideoGeneration[]> {
    const response = await api.get(`/projects/${projectId}/video-generations`)
    return response.data
  },

  async createVideoGeneration(projectId: number, data: VideoGenerationCreate): Promise<VideoGeneration> {
    const response = await api.post(`/projects/${projectId}/video-generations`, data)
    return response.data
  }
}