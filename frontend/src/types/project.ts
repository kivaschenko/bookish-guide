export type ProjectStatus = 'draft' | 'processing' | 'completed' | 'error'
export type VideoGenerationStage = 'script' | 'voice' | 'broll' | 'assembly' | 'complete'
export type VideoGenerationStatus = 'pending' | 'processing' | 'completed' | 'error'

export interface Project {
  id: number
  name: string
  description?: string
  status: ProjectStatus
  input_text?: string
  language: string
  project_path?: string
  created_at: string
  updated_at: string
  user_id: number
}

export interface ProjectCreate {
  name: string
  description?: string
  input_text?: string
  language?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  input_text?: string
  language?: string
  status?: ProjectStatus
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
}

export interface VideoGeneration {
  id: number
  project_id: number
  stage: VideoGenerationStage
  status: VideoGenerationStatus
  progress_percentage: number
  error_message?: string
  timeline_data?: any
  output_files?: any
  created_at: string
  updated_at: string
}

export interface VideoGenerationCreate {
  stage?: VideoGenerationStage
  force_restart?: boolean
}