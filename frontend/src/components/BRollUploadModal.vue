<template>
  <div class="modal fade show" style="display: block;" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Upload B-roll</h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleSubmit">
            <!-- File Upload -->
            <div class="mb-3">
              <label class="form-label">Select Files</label>
              <input
                type="file"
                class="form-control"
                ref="fileInput"
                @change="handleFileSelect"
                multiple
                accept="video/*,image/*"
                required
              />
              <div class="form-text">
                Supported formats: MP4, MOV, AVI, WEBM, JPG, PNG, GIF. Max size: 100MB per file.
              </div>
            </div>

            <!-- Preview Selected Files -->
            <div v-if="selectedFiles.length > 0" class="mb-3">
              <label class="form-label">Selected Files ({{ selectedFiles.length }})</label>
              <div class="row g-2">
                <div 
                  v-for="(file, index) in selectedFiles" 
                  :key="index"
                  class="col-md-6"
                >
                  <div class="card">
                    <div class="card-body py-2">
                      <div class="d-flex align-items-center">
                        <i class="fas fa-file me-2"></i>
                        <div class="flex-grow-1">
                          <div class="fw-medium">{{ file.name }}</div>
                          <small class="text-muted">{{ formatFileSize(file.size) }}</small>
                        </div>
                        <button 
                          type="button" 
                          class="btn btn-sm btn-outline-danger"
                          @click="removeFile(index)"
                        >
                          <i class="fas fa-times"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Upload Progress -->
            <div v-if="isUploading" class="mb-3">
              <label class="form-label">Upload Progress</label>
              <div class="progress">
                <div 
                  class="progress-bar" 
                  :style="{ width: uploadProgress + '%' }"
                  :class="uploadProgress === 100 ? 'bg-success' : 'bg-primary'"
                >
                  {{ uploadProgress }}%
                </div>
              </div>
              <div v-if="currentUploadFile" class="mt-1">
                <small class="text-muted">
                  Uploading: {{ currentUploadFile }} ({{ currentFileIndex }}/{{ selectedFiles.length }})
                </small>
              </div>
            </div>

            <!-- Bulk Metadata -->
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
                  <label class="form-label">License</label>
                  <select class="form-select" v-model="formData.license">
                    <option value="royalty_free">Royalty Free</option>
                    <option value="creative_commons">Creative Commons</option>
                    <option value="public_domain">Public Domain</option>
                    <option value="commercial">Commercial</option>
                    <option value="personal">Personal Use</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Description (Optional)</label>
              <textarea 
                class="form-control" 
                v-model="formData.description"
                rows="3"
                placeholder="Describe the content of these B-roll files..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Tags (Optional)</label>
              <input
                type="text"
                class="form-control"
                v-model="tagsInput"
                placeholder="Enter tags separated by commas (e.g., sunset, ocean, peaceful)"
              />
              <div class="form-text">
                Tags help make your B-roll searchable. Separate multiple tags with commas.
              </div>
            </div>

            <!-- Advanced Options -->
            <div class="card bg-light">
              <div class="card-header py-2">
                <h6 class="mb-0">
                  <button 
                    type="button" 
                    class="btn btn-link p-0 text-decoration-none"
                    @click="showAdvanced = !showAdvanced"
                  >
                    <i class="fas" :class="showAdvanced ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
                    Advanced Options
                  </button>
                </h6>
              </div>
              <div v-show="showAdvanced" class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label class="form-label">Quality</label>
                      <select class="form-select" v-model="formData.quality">
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label class="form-label">Mood</label>
                      <input
                        type="text"
                        class="form-control"
                        v-model="formData.mood"
                        placeholder="e.g., calm, energetic, dramatic"
                      />
                    </div>
                  </div>
                </div>
                <div class="row">
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label class="form-label">Source URL (Optional)</label>
                      <input
                        type="url"
                        class="form-control"
                        v-model="formData.source_url"
                        placeholder="https://..."
                      />
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label class="form-label">Attribution (Optional)</label>
                      <input
                        type="text"
                        class="form-control"
                        v-model="formData.attribution"
                        placeholder="Creator name or source"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')" :disabled="isUploading">
            Cancel
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="handleSubmit"
            :disabled="selectedFiles.length === 0 || isUploading || !formData.category"
          >
            <span v-if="isUploading" class="spinner-border spinner-border-sm me-2"></span>
            {{ isUploading ? 'Uploading...' : `Upload ${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''}` }}
          </button>
        </div>
      </div>
    </div>
  </div>
  <div class="modal-backdrop fade show"></div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBRollStore } from '@/stores/broll'
import { useNotificationStore } from '@/stores/notification'

const emit = defineEmits<{
  close: []
  uploaded: []
}>()

const brollStore = useBRollStore()
const notificationStore = useNotificationStore()

// State
const fileInput = ref<HTMLInputElement>()
const selectedFiles = ref<File[]>([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const currentUploadFile = ref('')
const currentFileIndex = ref(0)
const showAdvanced = ref(false)
const tagsInput = ref('')

const formData = ref({
  category: '',
  license: 'royalty_free',
  description: '',
  quality: 'high',
  mood: '',
  source_url: '',
  attribution: ''
})

// Methods
const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    const files = Array.from(input.files)
    
    // Validate file sizes
    const maxSize = 100 * 1024 * 1024 // 100MB
    const validFiles = files.filter(file => {
      if (file.size > maxSize) {
        notificationStore.addNotification({
          message: `File "${file.name}" is too large. Maximum size is 100MB.`,
          type: 'error'
        })
        return false
      }
      return true
    })
    
    selectedFiles.value = validFiles
  }
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
  if (selectedFiles.value.length === 0 && fileInput.value) {
    fileInput.value.value = ''
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const handleSubmit = async () => {
  if (selectedFiles.value.length === 0 || !formData.value.category) {
    return
  }

  isUploading.value = true
  uploadProgress.value = 0
  currentFileIndex.value = 0

  try {
    const tags = tagsInput.value
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    for (let i = 0; i < selectedFiles.value.length; i++) {
      const file = selectedFiles.value[i]
      currentUploadFile.value = file.name
      currentFileIndex.value = i + 1

      // Use filename as title if not provided
      const title = file.name.replace(/\.[^/.]+$/, '') // Remove extension
      
      const uploadData = {
        title,
        description: formData.value.description || undefined,
        category: formData.value.category,
        tags: tags.length > 0 ? JSON.stringify(tags) : undefined,
        file
      }

      await brollStore.uploadBRoll(uploadData)
      
      // Update progress
      uploadProgress.value = Math.round(((i + 1) / selectedFiles.value.length) * 100)
    }

    notificationStore.addNotification({
      message: `Successfully uploaded ${selectedFiles.value.length} file${selectedFiles.value.length > 1 ? 's' : ''}`,
      type: 'success'
    })

    emit('uploaded')
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to upload some files. Please try again.',
      type: 'error'
    })
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
    currentUploadFile.value = ''
    currentFileIndex.value = 0
  }
}
</script>

<style scoped>
.modal-backdrop {
  background-color: rgba(0, 0, 0, 0.5);
}

.progress {
  height: 8px;
}

.card-header .btn-link {
  color: inherit;
}

.card-header .btn-link:hover {
  color: var(--bs-primary);
}
</style>