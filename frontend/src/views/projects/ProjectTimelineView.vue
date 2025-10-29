<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">Project Timeline</h1>
    <RouterLink :to="`/projects/${projectId}/edit`" class="btn btn-outline-secondary">
      <i class="fas fa-arrow-left me-2"></i>
      Back to Project
    </RouterLink>
  </div>

  <div v-if="projectStore.isLoading" class="text-center py-4">
    <div class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>

  <div v-else-if="!project" class="alert alert-danger">
    Project not found.
  </div>

  <div v-else>
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">{{ project.name }} - Timeline Editor</h5>
      </div>
      <div class="card-body">
        <div class="alert alert-info">
          <i class="fas fa-info-circle me-2"></i>
          <strong>Timeline Editor Coming Soon!</strong>
          <p class="mb-0 mt-2">
            The timeline editor will allow you to:
          </p>
          <ul class="mt-2 mb-0">
            <li>Edit B-roll video sequences</li>
            <li>Adjust timing and synchronization</li>
            <li>Add custom overlays and effects</li>
            <li>Preview the final video</li>
          </ul>
        </div>

        <div class="row">
          <div class="col-lg-8">
            <div class="card">
              <div class="card-header">
                <h6 class="mb-0">Video Timeline</h6>
              </div>
              <div class="card-body">
                <div class="bg-light p-4 text-center">
                  <i class="fas fa-film fa-3x text-muted mb-3"></i>
                  <p class="text-muted">Timeline editor interface will be displayed here</p>
                  <div class="btn-group">
                    <button class="btn btn-outline-primary">
                      <i class="fas fa-play me-2"></i>
                      Preview
                    </button>
                    <button class="btn btn-outline-success">
                      <i class="fas fa-download me-2"></i>
                      Export
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-4">
            <div class="card mb-3">
              <div class="card-header">
                <h6 class="mb-0">Project Status</h6>
              </div>
              <div class="card-body">
                <div class="d-flex align-items-center mb-2">
                  <span class="badge me-2" :class="getStatusBadgeClass(project.status)">
                    {{ project.status }}
                  </span>
                  <small class="text-muted">{{ formatDate(project.updated_at) }}</small>
                </div>
                <p class="small text-muted mb-0">
                  {{ getStatusDescription(project.status) }}
                </p>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h6 class="mb-0">Tools</h6>
              </div>
              <div class="card-body">
                <div class="d-grid gap-2">
                  <button class="btn btn-outline-primary">
                    <i class="fas fa-images me-2"></i>
                    B-roll Library
                  </button>
                  <button class="btn btn-outline-info">
                    <i class="fas fa-music me-2"></i>
                    Audio Tools
                  </button>
                  <button class="btn btn-outline-success">
                    <i class="fas fa-text-height me-2"></i>
                    Text Overlays
                  </button>
                  <button class="btn btn-outline-warning">
                    <i class="fas fa-palette me-2"></i>
                    Effects
                  </button>
                </div>
              </div>
            </div>
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

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'completed': return 'badge-completed'
    case 'processing': return 'badge-processing'
    case 'draft': return 'badge-draft'
    case 'error': return 'badge-error'
    default: return 'bg-secondary'
  }
}

const getStatusDescription = (status: string) => {
  switch (status) {
    case 'draft': return 'Project is in draft mode. Ready for editing.'
    case 'processing': return 'Video generation is in progress.'
    case 'completed': return 'Video generation completed successfully.'
    case 'error': return 'An error occurred during processing.'
    default: return 'Unknown status'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const loadProject = async () => {
  try {
    project.value = await projectStore.fetchProject(projectId.value)
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to load project',
      type: 'error'
    })
  }
}

onMounted(() => {
  loadProject()
})
</script>