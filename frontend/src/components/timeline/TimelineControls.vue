<template>
  <div class="timeline-controls">
    <div class="control-section">
      <!-- Playback Controls -->
      <div class="playback-controls">
        <button 
          class="btn btn-primary"
          @click="togglePlayback"
          :disabled="!hasTimeline"
        >
          <i :class="isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
        </button>
        
        <button 
          class="btn btn-outline-secondary"
          @click="stop"
          :disabled="!hasTimeline"
        >
          <i class="fas fa-stop"></i>
        </button>
        
        <button 
          class="btn btn-outline-secondary"
          @click="skipToStart"
          :disabled="!hasTimeline"
        >
          <i class="fas fa-step-backward"></i>
        </button>
        
        <button 
          class="btn btn-outline-secondary"
          @click="skipToEnd"
          :disabled="!hasTimeline"
        >
          <i class="fas fa-step-forward"></i>
        </button>
      </div>

      <!-- Time Display -->
      <div class="time-display">
        <span class="current-time">{{ formatTime(currentTime) }}</span>
        <span class="time-separator">/</span>
        <span class="total-time">{{ formatTime(totalDuration) }}</span>
      </div>

      <!-- Speed Control -->
      <div class="speed-control">
        <label class="form-label form-label-sm">Speed</label>
        <select 
          class="form-select form-select-sm"
          v-model="playbackSpeed"
          @change="onSpeedChange"
        >
          <option value="0.25">0.25x</option>
          <option value="0.5">0.5x</option>
          <option value="0.75">0.75x</option>
          <option value="1">1x</option>
          <option value="1.25">1.25x</option>
          <option value="1.5">1.5x</option>
          <option value="2">2x</option>
        </select>
      </div>
    </div>

    <!-- Timeline Scrubber -->
    <div class="timeline-scrubber">
      <div class="scrubber-track">
        <input 
          type="range"
          class="form-range"
          :min="0"
          :max="totalDuration"
          :step="0.1"
          :value="currentTime"
          @input="onScrubberChange"
          @mousedown="startScrubbing"
          @mouseup="stopScrubbing"
          :disabled="!hasTimeline"
        />
        
        <!-- Rush markers -->
        <div class="rush-markers">
          <div 
            v-for="(rush, rushId) in rushes" 
            :key="rushId"
            class="rush-marker"
            :style="getRushMarkerStyle(rush, rushId)"
            :title="`Rush ${rushId}: ${rush.message}`"
          >
            <span class="rush-label">{{ rushId }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Zoom Controls -->
    <div class="zoom-section">
      <div class="zoom-controls">
        <label class="form-label form-label-sm">Zoom</label>
        <div class="btn-group btn-group-sm">
          <button 
            class="btn btn-outline-secondary"
            @click="zoomOut"
            :disabled="zoomLevel <= minZoom"
          >
            <i class="fas fa-search-minus"></i>
          </button>
          
          <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
          
          <button 
            class="btn btn-outline-secondary"
            @click="zoomIn"
            :disabled="zoomLevel >= maxZoom"
          >
            <i class="fas fa-search-plus"></i>
          </button>
        </div>
        
        <button 
          class="btn btn-outline-secondary btn-sm ms-2"
          @click="fitToWindow"
        >
          Fit
        </button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-section">
      <button 
        class="btn btn-success"
        @click="previewVideo"
        :disabled="!hasTimeline || isSaving"
      >
        <i class="fas fa-eye me-1"></i>
        Preview
      </button>
      
      <button 
        class="btn btn-primary"
        @click="saveTimeline"
        :disabled="!hasChanges || isSaving"
      >
        <span v-if="isSaving" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="fas fa-save me-1"></i>
        {{ isSaving ? 'Saving...' : 'Save Changes' }}
      </button>
      
      <button 
        class="btn btn-warning"
        @click="exportVideo"
        :disabled="!hasTimeline"
      >
        <i class="fas fa-download me-1"></i>
        Export
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTimelineStore } from '@/stores/timeline'
import { useNotificationStore } from '@/stores/notification'

const timelineStore = useTimelineStore()
const notificationStore = useNotificationStore()

const playbackSpeed = ref(1)
const zoomLevel = ref(1)
const minZoom = 0.1
const maxZoom = 10
const isScrubbing = ref(false)
const isSaving = ref(false)
const playbackInterval = ref<ReturnType<typeof setInterval> | null>(null)

const hasTimeline = computed(() => !!timelineStore.state.timeline)
const hasChanges = computed(() => timelineStore.state.isDirty)
const isPlaying = computed(() => timelineStore.state.isPlaying)
const currentTime = computed(() => timelineStore.state.currentTime)
const totalDuration = computed(() => timelineStore.state.totalDuration)
const rushes = computed(() => timelineStore.rushes)

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 10)
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`
}

const togglePlayback = () => {
  timelineStore.togglePlayback()
  
  if (timelineStore.state.isPlaying) {
    startPlayback()
  } else {
    stopPlayback()
  }
}

const stop = () => {
  timelineStore.pause()
  timelineStore.setCurrentTime(0)
  stopPlayback()
}

const skipToStart = () => {
  timelineStore.setCurrentTime(0)
}

const skipToEnd = () => {
  timelineStore.setCurrentTime(totalDuration.value)
}

const startPlayback = () => {
  if (playbackInterval.value) {
    clearInterval(playbackInterval.value)
  }
  
  playbackInterval.value = setInterval(() => {
    if (timelineStore.state.isPlaying && !isScrubbing.value) {
      const newTime = timelineStore.state.currentTime + (0.1 * playbackSpeed.value)
      
      if (newTime >= totalDuration.value) {
        timelineStore.pause()
        timelineStore.setCurrentTime(totalDuration.value)
        stopPlayback()
      } else {
        timelineStore.setCurrentTime(newTime)
      }
    }
  }, 100) // Update every 100ms
}

const stopPlayback = () => {
  if (playbackInterval.value) {
    clearInterval(playbackInterval.value)
    playbackInterval.value = null
  }
}

const onSpeedChange = () => {
  // Restart playback with new speed if currently playing
  if (timelineStore.state.isPlaying) {
    stopPlayback()
    startPlayback()
  }
}

const onScrubberChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const newTime = parseFloat(input.value)
  timelineStore.setCurrentTime(newTime)
}

const startScrubbing = () => {
  isScrubbing.value = true
  if (timelineStore.state.isPlaying) {
    stopPlayback()
  }
}

const stopScrubbing = () => {
  isScrubbing.value = false
  if (timelineStore.state.isPlaying) {
    startPlayback()
  }
}

const getRushMarkerStyle = (rush: any, rushId: string) => {
  // Calculate position based on rush timing
  let startTime = 0
  const rushIds = Object.keys(rushes.value)
  const rushIndex = rushIds.indexOf(rushId)
  
  for (let i = 0; i < rushIndex; i++) {
    const prevRush = rushes.value[rushIds[i]]
    if (prevRush) {
      startTime += prevRush.duration
    }
  }
  
  const leftPercent = (startTime / totalDuration.value) * 100
  const widthPercent = (rush.duration / totalDuration.value) * 100
  
  return {
    left: `${leftPercent}%`,
    width: `${widthPercent}%`
  }
}

const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value * 1.5, maxZoom)
  emit('zoomChanged', zoomLevel.value)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value / 1.5, minZoom)
  emit('zoomChanged', zoomLevel.value)
}

const fitToWindow = () => {
  zoomLevel.value = 1
  emit('zoomChanged', zoomLevel.value)
}

const saveTimeline = async () => {
  if (!hasChanges.value) return
  
  isSaving.value = true
  try {
    await timelineStore.saveTimeline()
    notificationStore.addNotification({
      message: 'Timeline saved successfully',
      type: 'success'
    })
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to save timeline',
      type: 'error'
    })
  } finally {
    isSaving.value = false
  }
}

const previewVideo = () => {
  // TODO: Implement video preview functionality
  notificationStore.addNotification({
    message: 'Video preview coming soon!',
    type: 'info'
  })
}

const exportVideo = () => {
  // TODO: Implement video export functionality
  notificationStore.addNotification({
    message: 'Video export coming soon!',
    type: 'info'
  })
}

const emit = defineEmits<{
  zoomChanged: [zoom: number]
}>()

// Keyboard shortcuts
const handleKeyPress = (event: KeyboardEvent) => {
  if (event.target && (event.target as Element).tagName.toLowerCase() === 'input') {
    return // Don't handle shortcuts when typing in inputs
  }
  
  switch (event.code) {
    case 'Space':
      event.preventDefault()
      togglePlayback()
      break
    case 'Home':
      event.preventDefault()
      skipToStart()
      break
    case 'End':
      event.preventDefault()
      skipToEnd()
      break
    case 'KeyS':
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault()
        saveTimeline()
      }
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
  stopPlayback()
})
</script>

<style scoped>
.timeline-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.playback-controls {
  display: flex;
  gap: 8px;
}

.playback-controls .btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.time-display {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  min-width: 120px;
}

.time-separator {
  color: #6c757d;
}

.speed-control {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 80px;
}

.timeline-scrubber {
  width: 100%;
}

.scrubber-track {
  position: relative;
  width: 100%;
}

.form-range {
  width: 100%;
  height: 8px;
  background: transparent;
}

.rush-markers {
  position: absolute;
  top: -24px;
  left: 0;
  right: 0;
  height: 20px;
  pointer-events: none;
}

.rush-marker {
  position: absolute;
  height: 20px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: white;
  font-weight: 600;
  border: 1px solid #0056b3;
  min-width: 40px;
}

.rush-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 4px;
}

.zoom-section {
  display: flex;
  align-items: center;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-level {
  min-width: 40px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #495057;
  padding: 4px 8px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.action-section {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.form-label-sm {
  font-size: 11px;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 2px;
}

@media (max-width: 768px) {
  .control-section {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .action-section {
    margin-left: 0;
    justify-content: center;
  }
  
  .playback-controls {
    justify-content: center;
  }
}
</style>