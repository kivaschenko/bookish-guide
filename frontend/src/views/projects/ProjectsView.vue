<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">Projects</h1>
    <RouterLink to="/projects/new" class="btn btn-primary">
      <i class="fas fa-plus me-2"></i>
      New Project
    </RouterLink>
  </div>

  <!-- Filters -->
  <div class="card mb-4">
    <div class="card-body">
      <div class="row align-items-end">
        <div class="col-md-3">
          <label for="statusFilter" class="form-label">Status</label>
          <select v-model="filters.status" id="statusFilter" class="form-select">
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="error">Error</option>
          </select>
        </div>
        <div class="col-md-6">
          <label for="searchInput" class="form-label">Search</label>
          <input 
            v-model="filters.search" 
            type="text" 
            id="searchInput"
            class="form-control" 
            placeholder="Search projects..."
          />
        </div>
        <div class="col-md-3">
          <button @click="loadProjects" class="btn btn-outline-primary">
            <i class="fas fa-search me-2"></i>
            Filter
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Projects List -->
  <div class="card">
    <div class="card-body">
      <div v-if="projectStore.isLoading" class="text-center py-4">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <div v-else-if="projects.length === 0" class="text-center py-4 text-muted">
        <i class="fas fa-folder-open fa-3x mb-3"></i>
        <p>No projects found. Create your first project!</p>
        <RouterLink to="/projects/new" class="btn btn-primary">
          Create Project
        </RouterLink>
      </div>

      <div v-else>
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Status</th>
                <th>Language</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="project in projects" :key="project.id">
                <td>
                  <strong>{{ project.name }}</strong>
                </td>
                <td>
                  <span class="text-muted">
                    {{ project.description || 'No description' }}
                  </span>
                </td>
                <td>
                  <span class="badge" :class="getStatusBadgeClass(project.status)">
                    {{ project.status }}
                  </span>
                </td>
                <td>{{ project.language }}</td>
                <td>{{ formatDate(project.created_at) }}</td>
                <td>{{ formatDate(project.updated_at) }}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <RouterLink
                      :to="`/projects/${project.id}/edit`"
                      class="btn btn-outline-primary"
                      title="Edit"
                    >
                      <i class="fas fa-edit"></i>
                    </RouterLink>
                    <RouterLink
                      :to="`/projects/${project.id}/timeline`"
                      class="btn btn-outline-info"
                      title="Timeline"
                    >
                      <i class="fas fa-film"></i>
                    </RouterLink>
                    <button
                      @click="confirmDelete(project)"
                      class="btn btn-outline-danger"
                      title="Delete"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <nav v-if="totalPages > 1" class="mt-4">
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: pagination.page <= 1 }">
              <button class="page-link" @click="changePage(pagination.page - 1)">
                Previous
              </button>
            </li>
            <li 
              v-for="page in visiblePages" 
              :key="page"
              class="page-item" 
              :class="{ active: page === pagination.page }"
            >
              <button 
                v-if="typeof page === 'number'"
                class="page-link" 
                @click="changePage(page)"
              >
                {{ page }}
              </button>
              <span v-else class="page-link">{{ page }}</span>
            </li>
            <li class="page-item" :class="{ disabled: pagination.page >= totalPages }">
              <button class="page-link" @click="changePage(pagination.page + 1)">
                Next
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>

  <!-- Delete Confirmation Modal -->
  <div v-if="projectToDelete" class="modal show d-block" style="background-color: rgba(0,0,0,0.5);">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Delete Project</h5>
          <button type="button" class="btn-close" @click="projectToDelete = null"></button>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to delete the project <strong>{{ projectToDelete.name }}</strong>?</p>
          <p class="text-danger small">This action cannot be undone.</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="projectToDelete = null">
            Cancel
          </button>
          <button type="button" class="btn btn-danger" @click="deleteProject">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useNotificationStore } from '@/stores/notification'
import type { Project } from '@/types/project'

const projectStore = useProjectStore()
const notificationStore = useNotificationStore()

const projects = ref<Project[]>([])
const projectToDelete = ref<Project | null>(null)
const total = ref(0)

const filters = ref({
  status: '',
  search: ''
})

const pagination = ref({
  page: 1,
  limit: 20
})

const totalPages = computed(() => Math.ceil(total.value / pagination.value.limit))
const visiblePages = computed(() => {
  const current = pagination.value.page
  const total = totalPages.value
  const delta = 2
  const range = []
  
  for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
    range.push(i)
  }
  
  if (current - delta > 2) {
    range.unshift('...')
  }
  if (current + delta < total - 1) {
    range.push('...')
  }
  
  range.unshift(1)
  if (total > 1) range.push(total)
  
  return range.filter((v, i, a) => a.indexOf(v) === i)
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
  return date.toLocaleDateString()
}

const loadProjects = async () => {
  try {
    const response = await projectStore.fetchProjects({
      skip: (pagination.value.page - 1) * pagination.value.limit,
      limit: pagination.value.limit,
      status_filter: filters.value.status || undefined
    })
    projects.value = response.projects
    total.value = response.total
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to load projects',
      type: 'error'
    })
  }
}

const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    pagination.value.page = page
    loadProjects()
  }
}

const confirmDelete = (project: Project) => {
  projectToDelete.value = project
}

const deleteProject = async () => {
  if (!projectToDelete.value) return
  
  try {
    await projectStore.deleteProject(projectToDelete.value.id)
    notificationStore.addNotification({
      message: `Project "${projectToDelete.value.name}" deleted successfully`,
      type: 'success'
    })
    projectToDelete.value = null
    loadProjects()
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to delete project',
      type: 'error'
    })
  }
}

// Watch for filter changes
watch([filters], () => {
  pagination.value.page = 1
  loadProjects()
}, { deep: true })

onMounted(() => {
  loadProjects()
})
</script>