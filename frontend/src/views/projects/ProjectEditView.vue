<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">Edit Project</h1>
    <div>
      <RouterLink :to="`/projects/${projectId}/timeline`" class="btn btn-outline-info me-2">
        <i class="fas fa-film me-2"></i>
        Timeline
      </RouterLink>
      <RouterLink to="/projects" class="btn btn-outline-secondary">
        <i class="fas fa-arrow-left me-2"></i>
        Back to Projects
      </RouterLink>
    </div>
  </div>

  <div v-if="projectStore.isLoading" class="text-center py-4">
    <div class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>

  <div v-else-if="!project" class="alert alert-danger">
    Project not found.
  </div>

  <div v-else class="row">
    <div class="col-lg-8">
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">Project Details</h5>
        </div>
        <div class="card-body">
          <form @submit.prevent="handleUpdate">
            <div class="row">
              <div class="col-md-8">
                <div class="form-floating mb-3">
                  <input
                    v-model="form.name"
                    type="text"
                    class="form-control"
                    id="projectName"
                    placeholder="Project Name"
                    required
                  />
                  <label for="projectName">Project Name</label>
                </div>
              </div>
              <div class="col-md-4">
                <div class="form-floating mb-3">
                  <select v-model="form.language" class="form-select" id="language">
                    <option value="english">English</option>
                    <option value="spanish">Spanish</option>
                    <option value="french">French</option>
                    <option value="german">German</option>
                    <option value="italian">Italian</option>
                  </select>
                  <label for="language">Language</label>
                </div>
              </div>
            </div>

            <div class="form-floating mb-3">
              <textarea
                v-model="form.description"
                class="form-control"
                id="description"
                style="height: 100px"
                placeholder="Project Description"
              ></textarea>
              <label for="description">Description</label>
            </div>

            <div class="form-floating mb-3">
              <select v-model="form.status" class="form-select" id="status">
                <option value="draft">Draft</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="error">Error</option>
              </select>
              <label for="status">Status</label>
            </div>

            <div class="form-floating mb-4">
              <textarea
                v-model="form.input_text"
                class="form-control"
                id="inputText"
                style="height: 200px"
                placeholder="Enter your video content..."
              ></textarea>
              <label for="inputText">Content / Script</label>
            </div>

            <div class="d-flex justify-content-between">
              <button
                type="button"
                @click="startVideoGeneration"
                class="btn btn-success"
                :disabled="!form.input_text || project.status === 'processing'"
              >
                <i class="fas fa-play me-2"></i>
                Generate Video
              </button>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="isLoading"
              >
                <span
                  v-if="isLoading"
                  class="spinner-border spinner-border-sm me-2"
                ></span>
                Update Project
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">Project Info</h5>
        </div>
        <div class="card-body">
          <dl class="row small">
            <dt class="col-sm-4">Created:</dt>
            <dd class="col-sm-8">{{ formatDate(project.created_at) }}</dd>
            
            <dt class="col-sm-4">Updated:</dt>
            <dd class="col-sm-8">{{ formatDate(project.updated_at) }}</dd>
            
            <dt class="col-sm-4">Status:</dt>
            <dd class="col-sm-8">
              <span class="badge" :class="getStatusBadgeClass(project.status)">
                {{ project.status }}
              </span>
            </dd>
            
            <dt class="col-sm-4">Language:</dt>
            <dd class="col-sm-8">{{ project.language }}</dd>
          </dl>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">Video Generation</h5>
        </div>
        <div class="card-body">
          <p class="small text-muted mb-3">
            Generate video content from your script using AI.
          </p>
          
          <div class="d-grid">
            <button
              @click="startVideoGeneration"
              class="btn btn-success"
              :disabled="!form.input_text || project.status === 'processing'"
            >
              <i class="fas fa-play me-2"></i>
              Start Generation
            </button>
          </div>
          
          <hr>
          
          <div class="small">
            <strong>Process Steps:</strong>
            <ol class="mt-2 mb-0">
              <li>Script Analysis</li>
              <li>Voice Synthesis</li>
              <li>B-roll Matching</li>
              <li>Video Assembly</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useNotificationStore } from '@/stores/notification'
import type { Project } from '@/types/project'

const route = useRoute()
const projectStore = useProjectStore()
const notificationStore = useNotificationStore()

const projectId = computed(() => parseInt(route.params.id as string))
const project = ref<Project | null>(null)
const isLoading = ref(false)

const form = ref({
  name: '',
  description: '',
  input_text: '',
  language: 'english',
  status: 'draft' as any
})

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'completed': return 'badge-completed'
    case 'processing': return 'badge-processing'
    case 'draft': return 'badge-draft'
    case 'error': return 'badge-error'
    default: return 'bg-secondary'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const loadProject = async () => {
  try {
    project.value = await projectStore.fetchProject(projectId.value)
    
    // Populate form
    form.value = {
      name: project.value.name,
      description: project.value.description || '',
      input_text: project.value.input_text || '',
      language: project.value.language,
      status: project.value.status
    }
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to load project',
      type: 'error'
    })
  }
}

const handleUpdate = async () => {
  if (!project.value) return
  
  try {
    isLoading.value = true
    await projectStore.updateProject(project.value.id, {
      name: form.value.name,
      description: form.value.description || undefined,
      input_text: form.value.input_text || undefined,
      language: form.value.language,
      status: form.value.status
    })
    
    notificationStore.addNotification({
      message: 'Project updated successfully',
      type: 'success'
    })
    
    // Reload project data
    await loadProject()
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to update project',
      type: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

const startVideoGeneration = async () => {
  if (!project.value || !form.value.input_text) return
  
  try {
    await projectStore.startVideoGeneration(project.value.id, {
      stage: 'script'
    })
    
    notificationStore.addNotification({
      message: 'Video generation started!',
      type: 'success'
    })
    
    // Update project status
    form.value.status = 'processing'
    await handleUpdate()
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to start video generation',
      type: 'error'
    })
  }
}

onMounted(() => {
  loadProject()
})
</script>