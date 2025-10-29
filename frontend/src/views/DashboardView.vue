<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">Dashboard</h1>
    <RouterLink to="/projects/new" class="btn btn-primary">
      <i class="fas fa-plus me-2"></i>
      New Project
    </RouterLink>
  </div>

  <!-- Statistics Cards -->
  <div class="row mb-4">
    <div class="col-md-3">
      <div class="card bg-primary text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Total Projects</h5>
              <h2 class="mb-0">{{ stats.totalProjects }}</h2>
            </div>
            <i class="fas fa-folder fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-success text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Completed</h5>
              <h2 class="mb-0">{{ stats.completedProjects }}</h2>
            </div>
            <i class="fas fa-check-circle fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-warning text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Processing</h5>
              <h2 class="mb-0">{{ stats.processingProjects }}</h2>
            </div>
            <i class="fas fa-cog fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-info text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Draft</h5>
              <h2 class="mb-0">{{ stats.draftProjects }}</h2>
            </div>
            <i class="fas fa-edit fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- B-roll Statistics -->
  <div class="row mb-4" v-if="brollStats">
    <div class="col-12">
      <h5 class="mb-3">B-roll Library</h5>
    </div>
    <div class="col-md-3">
      <div class="card bg-purple text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h6 class="card-title">Total Files</h6>
              <h3 class="mb-0">{{ brollStats.user_stats.total_files }}</h3>
            </div>
            <i class="fas fa-file-video fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-teal text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h6 class="card-title">Videos</h6>
              <h3 class="mb-0">{{ brollStats.user_stats.video_files }}</h3>
            </div>
            <i class="fas fa-video fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-indigo text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h6 class="card-title">Images</h6>
              <h3 class="mb-0">{{ brollStats.user_stats.image_files }}</h3>
            </div>
            <i class="fas fa-image fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-orange text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h6 class="card-title">Storage</h6>
              <h3 class="mb-0">{{ brollStats.user_stats.total_size_mb }}MB</h3>
            </div>
            <i class="fas fa-hdd fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Recent Projects -->
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h5 class="mb-0">Recent Projects</h5>
      <RouterLink to="/projects" class="btn btn-sm btn-outline-primary">
        View All
      </RouterLink>
    </div>
    <div class="card-body">
      <div v-if="isLoading" class="text-center py-4">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <div v-else-if="recentProjects.length === 0" class="text-center py-4 text-muted">
        <i class="fas fa-folder-open fa-3x mb-3"></i>
        <p>No projects yet. Create your first project to get started!</p>
        <RouterLink to="/projects/new" class="btn btn-primary">
          Create Project
        </RouterLink>
      </div>

      <div v-else class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Language</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="project in recentProjects" :key="project.id">
              <td>
                <div>
                  <strong>{{ project.name }}</strong>
                  <div class="text-muted small" v-if="project.description">
                    {{ project.description }}
                  </div>
                </div>
              </td>
              <td>
                <span class="badge" :class="getStatusBadgeClass(project.status)">
                  {{ project.status }}
                </span>
              </td>
              <td>{{ project.language }}</td>
              <td>{{ formatDate(project.updated_at) }}</td>
              <td>
                <div class="btn-group btn-group-sm">
                  <RouterLink
                    :to="`/projects/${project.id}/edit`"
                    class="btn btn-outline-primary"
                  >
                    <i class="fas fa-edit"></i>
                  </RouterLink>
                  <RouterLink
                    :to="`/projects/${project.id}/timeline`"
                    class="btn btn-outline-info"
                  >
                    <i class="fas fa-film"></i>
                  </RouterLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useBRollStore } from '@/stores/broll'
import type { Project } from '@/types/project'
import type { StorageStats } from '@/services/brollApi'

const projectStore = useProjectStore()
const brollStore = useBRollStore()

const isLoading = ref(false)
const recentProjects = ref<Project[]>([])
const brollStats = ref<StorageStats | null>(null)

const stats = computed(() => {
  const projects = recentProjects.value
  return {
    totalProjects: projects.length,
    completedProjects: projects.filter(p => p.status === 'completed').length,
    processingProjects: projects.filter(p => p.status === 'processing').length,
    draftProjects: projects.filter(p => p.status === 'draft').length,
  }
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

const loadRecentProjects = async () => {
  isLoading.value = true
  try {
    const response = await projectStore.fetchProjects({ limit: 10 })
    recentProjects.value = response.projects
  } catch (error) {
    console.error('Failed to load projects:', error)
  } finally {
    isLoading.value = false
  }
}

const loadBRollStats = async () => {
  try {
    await brollStore.fetchStorageStats()
    brollStats.value = brollStore.storageStats
  } catch (error) {
    console.error('Failed to load B-roll stats:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    loadRecentProjects(),
    loadBRollStats()
  ])
})
</script>

<style scoped>
.bg-purple {
  background-color: #8b5cf6 !important;
}

.bg-teal {
  background-color: #06b6d4 !important;
}

.bg-indigo {
  background-color: #6366f1 !important;
}

.bg-orange {
  background-color: #f97316 !important;
}

.badge-completed {
  background-color: #10b981;
  color: white;
}

.badge-processing {
  background-color: #f59e0b;
  color: white;
}

.badge-draft {
  background-color: #6b7280;
  color: white;
}

.badge-error {
  background-color: #ef4444;
  color: white;
}
</style>