<template>
  <div class="clip-editor" v-if="clip">
    <div class="card">
      <div class="card-header">
        <h6 class="mb-0">
          <i class="fas fa-video me-2"></i>
          Edit Clip: {{ getClipName(clip.video) }}
        </h6>
      </div>
      
      <div class="card-body">
        <!-- Basic Properties -->
        <div class="section mb-4">
          <h6 class="section-title">Timing & Properties</h6>
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label">Start Time (s)</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                :value="clip.start"
                @input="updateClip({ start: parseFloat(($event.target as HTMLInputElement).value) })"
                step="0.1"
                min="0"
              />
            </div>
            <div class="col-md-4">
              <label class="form-label">Duration (s)</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                :value="clip.duration"
                @input="updateClip({ duration: parseFloat(($event.target as HTMLInputElement).value) })"
                step="0.1"
                min="0.1"
              />
            </div>
            <div class="col-md-4">
              <label class="form-label">Score</label>
              <div class="input-group">
                <input 
                  type="number" 
                  class="form-control form-control-sm"
                  :value="clip.score"
                  @input="updateClip({ score: parseFloat(($event.target as HTMLInputElement).value) })"
                  step="0.01"
                  min="0"
                  max="1"
                />
                <span class="input-group-text">{{ Math.round(clip.score * 100) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Effects Section -->
        <div class="section mb-4">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="section-title mb-0">Effects</h6>
            <div class="dropdown">
              <button 
                class="btn btn-sm btn-outline-primary dropdown-toggle"
                type="button"
                data-bs-toggle="dropdown"
              >
                <i class="fas fa-plus me-1"></i>
                Add Effect
              </button>
              <ul class="dropdown-menu">
                <li><a class="dropdown-item" @click="addEffect('fade')">Fade In/Out</a></li>
                <li><a class="dropdown-item" @click="addEffect('zoom')">Zoom</a></li>
                <li><a class="dropdown-item" @click="addEffect('slide')">Slide</a></li>
                <li><a class="dropdown-item" @click="addEffect('blur')">Blur</a></li>
                <li><a class="dropdown-item" @click="addEffect('color_correction')">Color Correction</a></li>
              </ul>
            </div>
          </div>
          
          <div v-if="effects.length === 0" class="text-muted text-center py-3">
            No effects applied
          </div>
          
          <div v-else class="effects-list">
            <div 
              v-for="(effect, index) in effects" 
              :key="index"
              class="effect-item"
            >
              <div class="effect-header">
                <span class="effect-type">{{ formatEffectType(effect.type) }}</span>
                <button 
                  class="btn btn-sm btn-outline-danger"
                  @click="removeEffect(index)"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
              
              <div class="effect-controls">
                <div class="row g-2">
                  <div class="col-6">
                    <label class="form-label form-label-sm">Start Time</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="effect.start_time"
                      @input="updateEffect(index, { start_time: parseFloat(($event.target as HTMLInputElement).value) })"
                      step="0.1"
                      min="0"
                    />
                  </div>
                  <div class="col-6">
                    <label class="form-label form-label-sm">Duration</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="effect.duration"
                      @input="updateEffect(index, { duration: parseFloat(($event.target as HTMLInputElement).value) })"
                      step="0.1"
                      min="0.1"
                    />
                  </div>
                </div>
                
                <!-- Effect-specific parameters -->
                <div v-if="effect.type === 'fade'" class="mt-2">
                  <label class="form-label form-label-sm">Fade Type</label>
                  <select 
                    class="form-select form-select-sm"
                    :value="effect.parameters?.fadeType || 'in'"
                    @change="updateEffectParameter(index, 'fadeType', ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="in">Fade In</option>
                    <option value="out">Fade Out</option>
                    <option value="inout">Fade In & Out</option>
                  </select>
                </div>
                
                <div v-if="effect.type === 'zoom'" class="mt-2">
                  <div class="row g-2">
                    <div class="col-6">
                      <label class="form-label form-label-sm">Scale</label>
                      <input 
                        type="number" 
                        class="form-control form-control-sm"
                        :value="effect.parameters?.scale || 1.2"
                        @input="updateEffectParameter(index, 'scale', parseFloat(($event.target as HTMLInputElement).value))"
                        step="0.1"
                        min="0.1"
                        max="5"
                      />
                    </div>
                    <div class="col-6">
                      <label class="form-label form-label-sm">Direction</label>
                      <select 
                        class="form-select form-select-sm"
                        :value="effect.parameters?.direction || 'in'"
                        @change="updateEffectParameter(index, 'direction', ($event.target as HTMLSelectElement).value)"
                      >
                        <option value="in">Zoom In</option>
                        <option value="out">Zoom Out</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Overlays Section -->
        <div class="section mb-4">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="section-title mb-0">Overlays</h6>
            <div class="dropdown">
              <button 
                class="btn btn-sm btn-outline-info dropdown-toggle"
                type="button"
                data-bs-toggle="dropdown"
              >
                <i class="fas fa-plus me-1"></i>
                Add Overlay
              </button>
              <ul class="dropdown-menu">
                <li><a class="dropdown-item" @click="addOverlay('text')">Text</a></li>
                <li><a class="dropdown-item" @click="addOverlay('image')">Image</a></li>
                <li><a class="dropdown-item" @click="addOverlay('logo')">Logo</a></li>
              </ul>
            </div>
          </div>
          
          <div v-if="overlays.length === 0" class="text-muted text-center py-3">
            No overlays applied
          </div>
          
          <div v-else class="overlays-list">
            <div 
              v-for="(overlay, index) in overlays" 
              :key="index"
              class="overlay-item"
            >
              <div class="overlay-header">
                <span class="overlay-type">{{ formatOverlayType(overlay.type) }}</span>
                <button 
                  class="btn btn-sm btn-outline-danger"
                  @click="removeOverlay(index)"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
              
              <div class="overlay-controls">
                <div class="row g-2 mb-2">
                  <div class="col-6">
                    <label class="form-label form-label-sm">Start Time</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="overlay.start_time"
                      @input="updateOverlay(index, { start_time: parseFloat(($event.target as HTMLInputElement).value) })"
                      step="0.1"
                      min="0"
                    />
                  </div>
                  <div class="col-6">
                    <label class="form-label form-label-sm">Duration</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="overlay.duration"
                      @input="updateOverlay(index, { duration: parseFloat(($event.target as HTMLInputElement).value) })"
                      step="0.1"
                      min="0.1"
                    />
                  </div>
                </div>
                
                <div v-if="overlay.type === 'text'" class="mb-2">
                  <label class="form-label form-label-sm">Text Content</label>
                  <textarea 
                    class="form-control form-control-sm"
                    rows="2"
                    :value="overlay.content"
                    @input="updateOverlay(index, { content: ($event.target as HTMLTextAreaElement).value })"
                    placeholder="Enter text content..."
                  ></textarea>
                </div>
                
                <div v-if="overlay.type === 'image'" class="mb-2">
                  <label class="form-label form-label-sm">Image Upload</label>
                  <input 
                    type="file" 
                    class="form-control form-control-sm"
                    accept="image/*"
                    @change="handleImageUpload($event, index)"
                  />
                  <div v-if="overlay.content" class="mt-1">
                    <small class="text-success">Image: {{ overlay.content }}</small>
                  </div>
                </div>
                
                <!-- Position and Size -->
                <div class="row g-2">
                  <div class="col-3">
                    <label class="form-label form-label-sm">X Position</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="overlay.position.x"
                      @input="updateOverlayPosition(index, 'x', parseInt(($event.target as HTMLInputElement).value))"
                      min="0"
                    />
                  </div>
                  <div class="col-3">
                    <label class="form-label form-label-sm">Y Position</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="overlay.position.y"
                      @input="updateOverlayPosition(index, 'y', parseInt(($event.target as HTMLInputElement).value))"
                      min="0"
                    />
                  </div>
                  <div class="col-3">
                    <label class="form-label form-label-sm">Width</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="overlay.size.width"
                      @input="updateOverlaySize(index, 'width', parseInt(($event.target as HTMLInputElement).value))"
                      min="1"
                    />
                  </div>
                  <div class="col-3">
                    <label class="form-label form-label-sm">Height</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm"
                      :value="overlay.size.height"
                      @input="updateOverlaySize(index, 'height', parseInt(($event.target as HTMLInputElement).value))"
                      min="1"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- File Upload for Image Overlays -->
        <div v-if="showImageUpload" class="section">
          <h6 class="section-title">Upload Image Overlay</h6>
          <div class="upload-area">
            <input 
              type="file" 
              ref="fileInput"
              class="form-control"
              accept="image/*"
              @change="handleFileUpload"
            />
            <button 
              class="btn btn-primary mt-2"
              @click="uploadImage"
              :disabled="!selectedFile || isUploading"
            >
              <span v-if="isUploading" class="spinner-border spinner-border-sm me-2"></span>
              {{ isUploading ? 'Uploading...' : 'Upload Image' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTimelineStore } from '@/stores/timeline'
import type { BrollClip, EffectConfig, OverlayConfig } from '@/services/timelineApi'

interface Props {
  rushId: string
  clipIndex: number
}

const props = defineProps<Props>()
const timelineStore = useTimelineStore()

const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File>()
const isUploading = ref(false)
const showImageUpload = ref(false)

const clip = computed(() => {
  if (!timelineStore.state.timeline) return null
  const rush = timelineStore.state.timeline.rushes[props.rushId]
  return rush?.brolls[props.clipIndex] || null
})

const effects = computed(() => {
  const key = `${props.rushId}-${props.clipIndex}`
  return timelineStore.state.effects[key] || []
})

const overlays = computed(() => {
  const key = `${props.rushId}-${props.clipIndex}`
  return timelineStore.state.overlays[key] || []
})

const getClipName = (videoPath: string) => {
  return videoPath.split('/').pop()?.replace(/\.[^/.]+$/, "") || 'Unknown'
}

const updateClip = (updates: Partial<BrollClip>) => {
  timelineStore.updateClipTiming(props.rushId, props.clipIndex, updates)
}

const addEffect = (type: EffectConfig['type']) => {
  const effect: EffectConfig = {
    type,
    duration: 1.0,
    start_time: 0,
    parameters: getDefaultEffectParameters(type)
  }
  timelineStore.addEffect(props.rushId, props.clipIndex, effect)
}

const removeEffect = (effectIndex: number) => {
  timelineStore.removeEffect(props.rushId, props.clipIndex, effectIndex)
}

const updateEffect = (effectIndex: number, updates: Partial<EffectConfig>) => {
  const effect = effects.value[effectIndex]
  if (effect) {
    Object.assign(effect, updates)
  }
}

const updateEffectParameter = (effectIndex: number, paramName: string, value: any) => {
  const effect = effects.value[effectIndex]
  if (effect) {
    if (!effect.parameters) effect.parameters = {}
    effect.parameters[paramName] = value
  }
}

const addOverlay = (type: OverlayConfig['type']) => {
  const overlay: OverlayConfig = {
    type,
    content: type === 'text' ? 'Sample Text' : '',
    position: { x: 50, y: 50 },
    size: { width: 200, height: 50 },
    start_time: 0,
    duration: clip.value?.duration || 1.0
  }
  timelineStore.addOverlay(props.rushId, props.clipIndex, overlay)
}

const removeOverlay = (overlayIndex: number) => {
  timelineStore.removeOverlay(props.rushId, props.clipIndex, overlayIndex)
}

const updateOverlay = (overlayIndex: number, updates: Partial<OverlayConfig>) => {
  const overlay = overlays.value[overlayIndex]
  if (overlay) {
    Object.assign(overlay, updates)
  }
}

const updateOverlayPosition = (overlayIndex: number, axis: 'x' | 'y', value: number) => {
  const overlay = overlays.value[overlayIndex]
  if (overlay) {
    overlay.position[axis] = value
  }
}

const updateOverlaySize = (overlayIndex: number, dimension: 'width' | 'height', value: number) => {
  const overlay = overlays.value[overlayIndex]
  if (overlay) {
    overlay.size[dimension] = value
  }
}

const handleImageUpload = async (event: Event, overlayIndex: number) => {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  isUploading.value = true

  try {
    const result = await timelineStore.uploadOverlayImage(file, props.clipIndex)
    if (result.success && result.file_path) {
      updateOverlay(overlayIndex, { content: result.file_path })
    }
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    isUploading.value = false
  }
}

const formatEffectType = (type: string) => {
  return type.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const formatOverlayType = (type: string) => {
  return type.charAt(0).toUpperCase() + type.slice(1)
}

const getDefaultEffectParameters = (type: EffectConfig['type']) => {
  switch (type) {
    case 'fade':
      return { fadeType: 'in' }
    case 'zoom':
      return { scale: 1.2, direction: 'in' }
    case 'slide':
      return { direction: 'left', distance: 100 }
    case 'blur':
      return { intensity: 0.5 }
    case 'color_correction':
      return { brightness: 0, contrast: 0, saturation: 0 }
    default:
      return {}
  }
}

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0]
}

const uploadImage = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  try {
    await timelineStore.uploadOverlayImage(selectedFile.value, props.clipIndex)
    selectedFile.value = undefined
    if (fileInput.value) fileInput.value.value = ''
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.section {
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 1rem;
}

.section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  color: #495057;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.form-label-sm {
  font-size: 0.875rem;
  font-weight: 500;
}

.effect-item,
.overlay-item {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  background: #f8f9fa;
}

.effect-header,
.overlay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.effect-type,
.overlay-type {
  font-weight: 600;
  color: #495057;
}

.effect-controls,
.overlay-controls {
  background: white;
  border-radius: 4px;
  padding: 8px;
}

.upload-area {
  border: 2px dashed #dee2e6;
  border-radius: 6px;
  padding: 20px;
  text-align: center;
}

.upload-area:hover {
  border-color: #007bff;
  background: #f8f9fa;
}
</style>