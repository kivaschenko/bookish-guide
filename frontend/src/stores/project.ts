import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { 
  Project, 
  ProjectCreate, 
  ProjectUpdate, 
  ProjectListResponse,
  VideoGeneration,
  VideoGenerationCreate
} from '@/types/project'
import { projectApi } from '@/services/projectApi'

export const useProjectStore = defineStore('project', () => {
  // State
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  const setError = (message: string) => {
    error.value = message
  }

  const clearError = () => {
    error.value = null
  }

  const fetchProjects = async (params?: { skip?: number; limit?: number; status_filter?: string }): Promise<ProjectListResponse> => {
    try {
      isLoading.value = true
      clearError()
      
      const response = await projectApi.getProjects(params)
      projects.value = response.projects
      
      return response
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch projects')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchProject = async (id: number): Promise<Project> => {
    try {
      isLoading.value = true
      clearError()
      
      const project = await projectApi.getProject(id)
      currentProject.value = project
      
      return project
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch project')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const createProject = async (data: ProjectCreate): Promise<Project> => {
    try {
      isLoading.value = true
      clearError()
      
      const project = await projectApi.createProject(data)
      projects.value.unshift(project)
      
      return project
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateProject = async (id: number, data: ProjectUpdate): Promise<Project> => {
    try {
      isLoading.value = true
      clearError()
      
      const project = await projectApi.updateProject(id, data)
      
      // Update in projects list
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = project
      }
      
      // Update current project if it's the same
      if (currentProject.value?.id === id) {
        currentProject.value = project
      }
      
      return project
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update project')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteProject = async (id: number): Promise<void> => {
    try {
      isLoading.value = true
      clearError()
      
      await projectApi.deleteProject(id)
      
      // Remove from projects list
      projects.value = projects.value.filter(p => p.id !== id)
      
      // Clear current project if it's the same
      if (currentProject.value?.id === id) {
        currentProject.value = null
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchVideoGenerations = async (projectId: number): Promise<VideoGeneration[]> => {
    try {
      const generations = await projectApi.getVideoGenerations(projectId)
      return generations
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch video generations')
      throw err
    }
  }

  const startVideoGeneration = async (projectId: number, data: VideoGenerationCreate): Promise<VideoGeneration> => {
    try {
      const generation = await projectApi.createVideoGeneration(projectId, data)
      return generation
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start video generation')
      throw err
    }
  }

  return {
    // State
    projects,
    currentProject,
    isLoading,
    error,
    
    // Actions
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    fetchVideoGenerations,
    startVideoGeneration,
    setError,
    clearError
  }
})