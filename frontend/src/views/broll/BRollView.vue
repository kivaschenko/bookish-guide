<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">B-roll Library</h1>
    <button class="btn btn-primary" @click="showUploadModal = true">
      <i class="fas fa-upload me-2"></i>
      Upload B-roll
    </button>
  </div>

  <!-- Storage Stats -->
  <div class="row mb-4" v-if="storageStats">
    <div class="col-md-3">
      <div class="card bg-primary text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Total Files</h5>
              <h2 class="mb-0">{{ storageStats.user_stats.total_files }}</h2>
            </div>
            <i class="fas fa-file-video fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-success text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Videos</h5>
              <h2 class="mb-0">{{ storageStats.user_stats.video_files }}</h2>
            </div>
            <i class="fas fa-video fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-info text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Images</h5>
              <h2 class="mb-0">{{ storageStats.user_stats.image_files }}</h2>
            </div>
            <i class="fas fa-image fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card bg-warning text-white">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="flex-grow-1">
              <h5 class="card-title">Storage</h5>
              <h2 class="mb-0">{{ storageStats.user_stats.total_size_mb }}MB</h2>
            </div>
            <i class="fas fa-hdd fa-2x opacity-75"></i>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Filters -->
  <div class="card mb-4">
    <div class="card-body">
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label">Search</label>
          <div class="input-group">
            <input
              type="text"
              class="form-control"
              placeholder="Search by title, description..."
              v-model="searchQuery"
              @keyup.enter="handleSearch"
            />
            <button class="btn btn-outline-secondary" type="button" @click="handleSearch">
              <i class="fas fa-search"></i>
            </button>
          </div>
        </div>
        <div class="col-md-3">
          <label class="form-label">Category</label>
          <select class="form-select" v-model="selectedCategory" @change="handleCategoryFilter">
            <option value="">All Categories</option>
            <option value="nature">Nature</option>
            <option value="urban">Urban</option>
            <option value="people">People</option>
            <option value="technology">Technology</option>
            <option value="business">Business</option>
            <option value="lifestyle">Lifestyle</option>
            <option value="abstract">Abstract</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label">Status</label>
          <select class="form-select" v-model="selectedStatus" @change="handleStatusFilter">
            <option value="">All Status</option>
            <option value="available">Available</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="error">Error</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="form-label">&nbsp;</label>
          <div>
            <button class="btn btn-outline-secondary w-100" @click="clearFilters">
              <i class="fas fa-times me-1"></i>
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- B-roll List -->
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h5 class="mb-0">B-roll Files</h5>
      <div class="d-flex align-items-center">
        <span class="text-muted me-3">{{ totalItems }} files</span>
        <div class="btn-group btn-group-sm">
          <button 
            class="btn btn-outline-secondary" 
            :class="{ active: viewMode === 'grid' }"
            @click="viewMode = 'grid'"
          >
            <i class="fas fa-th"></i>
          </button>
          <button 
            class="btn btn-outline-secondary" 
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
          >
            <i class="fas fa-list"></i>
          </button>
        </div>
      </div>
    </div>
    <div class="card-body">
      <div v-if="isLoading" class="text-center py-4">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <div v-else-if="brolls.length === 0" class="text-center py-4 text-muted">
        <i class="fas fa-film fa-3x mb-3"></i>
        <p>No B-roll files found. Upload your first video or image to get started!</p>
        <button class="btn btn-primary" @click="showUploadModal = true">
          Upload B-roll
        </button>
      </div>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="row g-3">
        <div v-for="broll in brolls" :key="broll.id" class="col-md-4 col-lg-3">
          <div class="card h-100">
            <div class="position-relative">
              <div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 200px;">
                <video 
                  v-if="broll.mime_type.startsWith('video/')"
                  :src="getFileUrl(broll.filename)"
                  class="img-fluid"
                  style="max-height: 100%; max-width: 100%;"
                  controls
                  preload="metadata"
                >
                </video>
                <img 
                  v-else-if="broll.mime_type.startsWith('image/')"
                  :src="getFileUrl(broll.filename)"
                  class="img-fluid"
                  style="max-height: 100%; max-width: 100%;"
                  :alt="broll.title"
                />
                <i v-else class="fas fa-file fa-3x text-muted"></i>
              </div>
              <span 
                class="badge position-absolute top-0 end-0 m-2"
                :class="getStatusBadgeClass(broll.status)"
              >
                {{ broll.status }}
              </span>
            </div>
            <div class="card-body">
              <h6 class="card-title">{{ broll.title }}</h6>
              <p class="card-text small text-muted" v-if="broll.description">
                {{ broll.description }}
              </p>
              <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">
                  {{ formatFileSize(broll.file_size) }}
                </small>
                <div class="btn-group btn-group-sm">
                  <button class="btn btn-outline-primary" @click="editBRoll(broll)">
                    <i class="fas fa-edit"></i>
                  </button>
                  <button class="btn btn-outline-danger" @click="confirmDelete(broll)">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </div>
              <div v-if="broll.tags && broll.tags.length > 0" class="mt-2">
                <span 
                  v-for="tag in getTagsArray(broll.tags).slice(0, 3)" 
                  :key="tag" 
                  class="badge bg-secondary me-1"
                >
                  {{ tag }}
                </span>
                <span v-if="getTagsArray(broll.tags).length > 3" class="text-muted small">
                  +{{ getTagsArray(broll.tags).length - 3 }} more
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- List View -->
      <div v-else class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Preview</th>
              <th>Title</th>
              <th>Category</th>
              <th>Size</th>
              <th>Status</th>
              <th>Upload Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="broll in brolls" :key="broll.id">
              <td>
                <div class="d-flex align-items-center justify-content-center bg-light" style="width: 60px; height: 40px;">
                  <video 
                    v-if="broll.mime_type.startsWith('video/')"
                    :src="getFileUrl(broll.filename)"
                    style="max-height: 100%; max-width: 100%;"
                    muted
                  >
                  </video>
                  <img 
                    v-else-if="broll.mime_type.startsWith('image/')"
                    :src="getFileUrl(broll.filename)"
                    style="max-height: 100%; max-width: 100%;"
                    :alt="broll.title"
                  />
                  <i v-else class="fas fa-file text-muted"></i>
                </div>
              </td>
              <td>
                <div>
                  <strong>{{ broll.title }}</strong>
                  <div class="text-muted small" v-if="broll.description">
                    {{ broll.description }}
                  </div>
                </div>
              </td>
              <td>
                <span class="badge bg-info">{{ broll.category }}</span>
              </td>
              <td>{{ formatFileSize(broll.file_size) }}</td>
              <td>
                <span class="badge" :class="getStatusBadgeClass(broll.status)">
                  {{ broll.status }}
                </span>
              </td>
              <td>{{ formatDate(broll.created_at) }}</td>
              <td>
                <div class="btn-group btn-group-sm">
                  <button class="btn btn-outline-primary" @click="editBRoll(broll)">
                    <i class="fas fa-edit"></i>
                  </button>
                  <button class="btn btn-outline-danger" @click="confirmDelete(broll)">
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
          <li class="page-item" :class="{ disabled: currentPage === 1 }">
            <button class="page-link" @click="changePage(currentPage - 1)" :disabled="currentPage === 1">
              Previous
            </button>
          </li>
          <li 
            v-for="page in visiblePages" 
            :key="page" 
            class="page-item" 
            :class="{ active: page === currentPage }"
          >
            <button class="page-link" @click="changePage(page)">{{ page }}</button>
          </li>
          <li class="page-item" :class="{ disabled: currentPage === totalPages }">
            <button class="page-link" @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">
              Next
            </button>
          </li>
        </ul>
      </nav>
    </div>
  </div>

  <!-- Upload Modal -->
  <BRollUploadModal 
    v-if="showUploadModal" 
    @close="showUploadModal = false"
    @uploaded="handleUploadSuccess"
  />

  <!-- Edit Modal -->
  <BRollEditModal 
    v-if="showEditModal && selectedBRoll" 
    :broll="selectedBRoll"
    @close="showEditModal = false"
    @updated="handleUpdateSuccess"
  />

  <!-- Delete Confirmation Modal -->
  <div 
    v-if="showDeleteModal" 
    class="modal fade show" 
    style="display: block;"
    tabindex="-1"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Confirm Delete</h5>
          <button type="button" class="btn-close" @click="showDeleteModal = false"></button>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to delete "{{ selectedBRoll?.title }}"?</p>
          <div class="form-check">
            <input 
              class="form-check-input" 
              type="checkbox" 
              v-model="permanentDelete" 
              id="permanentDelete"
            />
            <label class="form-check-label" for="permanentDelete">
              Permanently delete (cannot be undone)
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showDeleteModal = false">
            Cancel
          </button>
          <button type="button" class="btn btn-danger" @click="handleDelete">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showDeleteModal" class="modal-backdrop fade show"></div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useBRollStore } from '@/stores/broll'
import { useNotificationStore } from '@/stores/notification'
import type { BRoll } from '@/services/brollApi'
import BRollUploadModal from '@/components/BRollUploadModal.vue'
import BRollEditModal from '@/components/BRollEditModal.vue'

const brollStore = useBRollStore()
const notificationStore = useNotificationStore()

// State
const showUploadModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const selectedBRoll = ref<BRoll | null>(null)
const permanentDelete = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedStatus = ref('')

// Computed properties - Use storeToRefs to maintain reactivity
const { 
  brolls, 
  isLoading, 
  storageStats, 
  currentPage, 
  totalPages, 
  totalItems 
} = storeToRefs(brollStore)

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, currentPage.value + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Methods
const getFileUrl = (filename: string): string => {
  return brollStore.getFileUrl(filename)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

const getStatusBadgeClass = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'available':
      return 'bg-success'
    case 'processing':
      return 'bg-warning'
    case 'pending':
      return 'bg-info'
    case 'error':
      return 'bg-danger'
    default:
      return 'bg-secondary'
  }
}

const handleSearch = async () => {
  try {
    await brollStore.searchBRolls(searchQuery.value)
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to search B-roll files',
      type: 'error'
    })
  }
}

const handleCategoryFilter = async () => {
  try {
    await brollStore.filterByCategory(selectedCategory.value)
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to filter by category',
      type: 'error'
    })
  }
}

const handleStatusFilter = async () => {
  try {
    await brollStore.fetchBRolls({
      ...brollStore.filters,
      status: selectedStatus.value,
      page: 1
    })
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to filter by status',
      type: 'error'
    })
  }
}

const clearFilters = async () => {
  searchQuery.value = ''
  selectedCategory.value = ''
  selectedStatus.value = ''
  brollStore.clearFilters()
  try {
    await brollStore.fetchBRolls()
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to clear filters',
      type: 'error'
    })
  }
}

const changePage = async (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    try {
      await brollStore.changePage(page)
    } catch (error) {
      notificationStore.addNotification({
        message: 'Failed to change page',
        type: 'error'
      })
    }
  }
}

const editBRoll = (broll: BRoll) => {
  selectedBRoll.value = broll
  showEditModal.value = true
}

const confirmDelete = (broll: BRoll) => {
  selectedBRoll.value = broll
  permanentDelete.value = false
  showDeleteModal.value = true
}

const handleDelete = async () => {
  if (!selectedBRoll.value) return

  try {
    await brollStore.deleteBRoll(selectedBRoll.value.id, permanentDelete.value)
    notificationStore.addNotification({
      message: `B-roll "${selectedBRoll.value.title}" deleted successfully`,
      type: 'success'
    })
    showDeleteModal.value = false
    selectedBRoll.value = null
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to delete B-roll',
      type: 'error'
    })
  }
}

const handleUploadSuccess = () => {
  showUploadModal.value = false
  notificationStore.addNotification({
    message: 'B-roll uploaded successfully',
    type: 'success'
  })
}

const handleUpdateSuccess = () => {
  showEditModal.value = false
  notificationStore.addNotification({
    message: 'B-roll updated successfully',
    type: 'success'
  })
}

// Lifecycle
onMounted(async () => {
  try {
    await Promise.all([
      brollStore.fetchBRolls(),
      brollStore.fetchStorageStats()
    ])
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to load B-roll data',
      type: 'error'
    })
  }
})

// Tags parsing helper
const getTagsArray = (tagsString: string | null | string[]): string[] => {
  if (!tagsString) return []
  console.log('Parsing tags:', tagsString);
  
  // If tags are stored as array, handle the broken JSON array format
  if (Array.isArray(tagsString)) {
    // Check if it's the broken format like ["[\"cows\"", "\"farm\"", "\"field\"]"]
    if (tagsString.length > 0) {
      // Join all array elements and try to reconstruct the JSON
      const joinedString = tagsString.join(',')
      // Remove extra quotes and brackets to clean it up
      const cleanedString = joinedString
        .replace(/^\["?/, '[')  // Fix opening bracket
        .replace(/"?\]$/, ']')  // Fix closing bracket
        .replace(/","/g, '","')  // Ensure proper comma separation
        .replace(/\\"/g, '"')   // Remove escaped quotes
      
      console.log('Cleaned string:', cleanedString);
      
      try {
        const parsed = JSON.parse(cleanedString)
        if (Array.isArray(parsed)) {
          return parsed
        }
      } catch (e) {
        // Fallback: extract quoted strings manually
        const matches = joinedString.match(/"([^"]+)"/g)
        if (matches) {
          return matches.map(match => match.replace(/"/g, ''))
        }
        return tagsString.filter(tag => tag && typeof tag === 'string')
      }
    }
    return tagsString.filter(tag => tag && typeof tag === 'string')
  }
  
  // If tags is a string (JSON), try to parse it
  if (typeof tagsString === 'string') {
    if (tagsString.startsWith('[')) {
      console.log('Detected tags as JSON array');
      try {
        const parsed = JSON.parse(tagsString)
        if (Array.isArray(parsed)) {
          return parsed
        }
      } catch (e) {
        return [tagsString]
      }
    }
    // If tags are stored as comma-separated string, split them into an array
    if (tagsString.includes(',')) {
      return tagsString.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
    }
    // Otherwise, return single tag as array  
    return [tagsString]
  }
  
  return []
}
</script>

<style scoped>
.card-img-top {
  object-fit: cover;
}

.modal-backdrop {
  background-color: rgba(0, 0, 0, 0.5);
}
</style>