<template>
  <div class="modal fade show" style="display: block;" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Edit B-roll</h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleSubmit">
            <!-- Preview -->
            <div class="mb-3 text-center">
              <div class="bg-light d-flex align-items-center justify-content-center" style="height: 200px;">
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
            </div>

            <!-- Basic Information -->
            <div class="mb-3">
              <label class="form-label">Title</label>
              <input
                type="text"
                class="form-control"
                v-model="formData.title"
                required
              />
            </div>

            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea 
                class="form-control" 
                v-model="formData.description"
                rows="3"
                placeholder="Describe the content of this B-roll..."
              ></textarea>
            </div>

            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Category</label>
                  <select class="form-select" v-model="formData.category" required>
                    <option value="">Select Category</option>
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
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Visibility</label>
                  <select class="form-select" v-model="formData.is_public">
                    <option :value="false">Private</option>
                    <option :value="true">Public</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Tags</label>
              <input
                type="text"
                class="form-control"
                v-model="tagsInput"
                placeholder="Enter tags separated by commas"
              />
              <div class="form-text">
                Separate multiple tags with commas.
              </div>
            </div>

            <!-- File Information (Read-only) -->
            <div class="card bg-light">
              <div class="card-header py-2">
                <h6 class="mb-0">File Information</h6>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <strong>Filename:</strong><br>
                    <span class="text-muted">{{ broll.original_filename }}</span>
                  </div>
                  <div class="col-md-6">
                    <strong>Size:</strong><br>
                    <span class="text-muted">{{ formatFileSize(broll.file_size) }}</span>
                  </div>
                </div>
                <div class="row mt-2" v-if="broll.duration || (broll.width && broll.height)">
                  <div class="col-md-6" v-if="broll.duration">
                    <strong>Duration:</strong><br>
                    <span class="text-muted">{{ formatDuration(broll.duration) }}</span>
                  </div>
                  <div class="col-md-6" v-if="broll.width && broll.height">
                    <strong>Dimensions:</strong><br>
                    <span class="text-muted">{{ broll.width }} × {{ broll.height }}</span>
                  </div>
                </div>
                <div class="row mt-2">
                  <div class="col-md-6">
                    <strong>Status:</strong><br>
                    <span class="badge" :class="getStatusBadgeClass(broll.status)">
                      {{ broll.status }}
                    </span>
                  </div>
                  <div class="col-md-6">
                    <strong>Upload Date:</strong><br>
                    <span class="text-muted">{{ formatDate(broll.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- AI Analysis (if available) -->
            <div v-if="broll.ai_description || (broll.ai_tags && broll.ai_tags.length > 0)" class="card bg-info-subtle mt-3">
              <div class="card-header py-2">
                <h6 class="mb-0">
                  <i class="fas fa-robot me-2"></i>
                  AI Analysis
                </h6>
              </div>
              <div class="card-body">
                <div v-if="broll.ai_description" class="mb-2">
                  <strong>AI Description:</strong><br>
                  <span class="text-muted">{{ broll.ai_description }}</span>
                </div>
                <div v-if="broll.ai_tags && broll.ai_tags.length > 0">
                  <strong>AI Tags:</strong><br>
                  <span 
                    v-for="tag in broll.ai_tags" 
                    :key="tag" 
                    class="badge bg-info me-1"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')" :disabled="isUpdating">
            Cancel
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="handleSubmit"
            :disabled="isUpdating || !hasChanges"
          >
            <span v-if="isUpdating" class="spinner-border spinner-border-sm me-2"></span>
            {{ isUpdating ? 'Updating...' : 'Update B-roll' }}
          </button>
        </div>
      </div>
    </div>
  </div>
  <div class="modal-backdrop fade show"></div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBRollStore } from '@/stores/broll'
import { useNotificationStore } from '@/stores/notification'
import type { BRoll } from '@/services/brollApi'

const props = defineProps<{
  broll: BRoll
}>()

const emit = defineEmits<{
  close: []
  updated: []
}>()

const brollStore = useBRollStore()
const notificationStore = useNotificationStore()

// State
const isUpdating = ref(false)
const tagsInput = ref('')

const formData = ref({
  title: '',
  description: '',
  category: '',
  is_public: false,
})

// Computed
const hasChanges = computed(() => {
  const tags = tagsInput.value
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)

  const originalTags = props.broll.tags || []
  
  return (
    formData.value.title !== props.broll.title ||
    (formData.value.description || '') !== (props.broll.description || '') ||
    formData.value.category !== props.broll.category ||
    formData.value.is_public !== props.broll.is_public ||
    JSON.stringify(tags.sort()) !== JSON.stringify(originalTags.sort())
  )
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

const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
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

const handleSubmit = async () => {
  if (!hasChanges.value) return

  isUpdating.value = true

  try {
    const tags = tagsInput.value
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    const updateData = {
      title: formData.value.title,
      description: formData.value.description || undefined,
      category: formData.value.category,
      is_public: formData.value.is_public,
      tags: tags.length > 0 ? tags : undefined,
    }

    await brollStore.updateBRoll(props.broll.id, updateData)

    notificationStore.addNotification({
      message: 'B-roll updated successfully',
      type: 'success'
    })

    emit('updated')
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to update B-roll',
      type: 'error'
    })
  } finally {
    isUpdating.value = false
  }
}

// Initialize form data
onMounted(() => {
  formData.value = {
    title: props.broll.title,
    description: props.broll.description || '',
    category: props.broll.category,
    is_public: props.broll.is_public,
  }
  
  if (props.broll.tags && props.broll.tags.length > 0) {
    tagsInput.value = props.broll.tags.join(', ')
  }
})
</script>

<style scoped>
.modal-backdrop {
  background-color: rgba(0, 0, 0, 0.5);
}

.bg-info-subtle {
  background-color: rgba(13, 202, 240, 0.1);
}
</style>