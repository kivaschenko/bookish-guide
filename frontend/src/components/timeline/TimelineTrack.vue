<template>
  <div class="timeline-track" ref="trackRef">
    <div class="track-header">
      <h6 class="track-title mb-0">Rush {{ rushId }}</h6>
      <small class="text-muted">{{ formatDuration(rush.duration) }}</small>
    </div>
    
    <div 
      class="track-content" 
      :style="{ minWidth: `${timelineWidth}px` }"
      @click="handleTrackClick"
    >
      <div 
        v-for="(clip, index) in rush.brolls" 
        :key="index"
        class="clip"
        :class="{ 
          'selected': isClipSelected(index),
          'has-effects': hasEffects(index),
          'has-overlays': hasOverlays(index)
        }"
        :style="getClipStyle(clip, index)"
        @click.stop="selectClip(index)"
        @mousedown="startDrag(index, $event)"
      >
        <div class="clip-content">
          <div class="clip-header">
            <span class="clip-name">{{ getClipName(clip.video) }}</span>
            <span class="clip-score badge badge-sm" :class="getScoreBadgeClass(clip.score)">
              {{ Math.round(clip.score * 100) }}%
            </span>
          </div>
          
          <div class="clip-body">
            <div class="clip-info">
              <small>Start: {{ formatTime(clip.start) }}</small>
              <small>Duration: {{ formatTime(clip.duration) }}</small>
            </div>
            
            <!-- Effect indicators -->
            <div v-if="hasEffects(index)" class="effect-indicators">
              <i class="fas fa-magic text-warning" title="Has effects"></i>
            </div>
            
            <!-- Overlay indicators -->
            <div v-if="hasOverlays(index)" class="overlay-indicators">
              <i class="fas fa-layer-group text-info" title="Has overlays"></i>
            </div>
          </div>
          
          <!-- Resize handles -->
          <div class="resize-handle resize-left" @mousedown.stop="startResize(index, 'start', $event)"></div>
          <div class="resize-handle resize-right" @mousedown.stop="startResize(index, 'end', $event)"></div>
        </div>
      </div>
      
      <!-- Playhead -->
      <div 
        v-if="showPlayhead"
        class="playhead"
        :style="{ left: `${playheadPosition}px` }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTimelineStore } from '@/stores/timeline'
import type { Rush, BrollClip } from '@/services/timelineApi'

interface Props {
  rushId: string
  rush: Rush
  timelineWidth: number
  pixelsPerSecond: number
  currentTime: number
  showPlayhead: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  clipSelected: [rushId: string, clipIndex: number]
  clipMoved: [rushId: string, fromIndex: number, toIndex: number]
  clipResized: [rushId: string, clipIndex: number, updates: Partial<BrollClip>]
}>()

const timelineStore = useTimelineStore()
const trackRef = ref<HTMLElement>()

// Drag and resize state
const dragState = ref<{
  isDragging: boolean
  isResizing: boolean
  resizeType: 'start' | 'end' | null
  draggedClipIndex: number | null
  startX: number
  startTime: number
}>({
  isDragging: false,
  isResizing: false,
  resizeType: null,
  draggedClipIndex: null,
  startX: 0,
  startTime: 0
})

const isClipSelected = (index: number) => {
  return timelineStore.state.selectedClip?.rushId === props.rushId && 
         timelineStore.state.selectedClip?.clipIndex === index
}

const hasEffects = (index: number) => {
  const key = `${props.rushId}-${index}`
  return timelineStore.state.effects[key]?.length > 0
}

const hasOverlays = (index: number) => {
  const key = `${props.rushId}-${index}`
  return timelineStore.state.overlays[key]?.length > 0
}

const playheadPosition = computed(() => {
  return props.currentTime * props.pixelsPerSecond
})

const getClipStyle = (clip: BrollClip, index: number) => {
  const left = getClipStartPosition(index)
  const width = clip.duration * props.pixelsPerSecond
  
  return {
    left: `${left}px`,
    width: `${Math.max(width, 50)}px`, // Minimum width for visibility
  }
}

const getClipStartPosition = (index: number) => {
  let position = 0
  for (let i = 0; i < index; i++) {
    position += props.rush.brolls[i].duration * props.pixelsPerSecond
  }
  return position
}

const getClipName = (videoPath: string) => {
  return videoPath.split('/').pop()?.replace(/\.[^/.]+$/, "") || 'Unknown'
}

const getScoreBadgeClass = (score: number) => {
  if (score >= 0.8) return 'bg-success'
  if (score >= 0.6) return 'bg-warning'
  return 'bg-danger'
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatDuration = (seconds: number) => {
  return formatTime(seconds)
}

const selectClip = (index: number) => {
  emit('clipSelected', props.rushId, index)
}

const handleTrackClick = (event: MouseEvent) => {
  // If clicking on empty space, deselect clip
  if (event.target === event.currentTarget) {
    timelineStore.selectRush(props.rushId)
  }
}

const startDrag = (index: number, event: MouseEvent) => {
  dragState.value = {
    isDragging: true,
    isResizing: false,
    resizeType: null,
    draggedClipIndex: index,
    startX: event.clientX,
    startTime: 0
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  event.preventDefault()
}

const startResize = (index: number, type: 'start' | 'end', event: MouseEvent) => {
  const clip = props.rush.brolls[index]
  
  dragState.value = {
    isDragging: false,
    isResizing: true,
    resizeType: type,
    draggedClipIndex: index,
    startX: event.clientX,
    startTime: type === 'start' ? clip.start : clip.start + clip.duration
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  event.preventDefault()
}

const handleMouseMove = (event: MouseEvent) => {
  if (!dragState.value.isDragging && !dragState.value.isResizing) return
  
  const deltaX = event.clientX - dragState.value.startX
  const deltaTime = deltaX / props.pixelsPerSecond
  
  if (dragState.value.isResizing && dragState.value.draggedClipIndex !== null) {
    const clip = props.rush.brolls[dragState.value.draggedClipIndex]
    const updates: Partial<BrollClip> = {}
    
    if (dragState.value.resizeType === 'start') {
      const newStart = Math.max(0, dragState.value.startTime + deltaTime)
      const newDuration = clip.duration - (newStart - clip.start)
      if (newDuration > 0.1) { // Minimum duration
        updates.start = newStart
        updates.duration = newDuration
      }
    } else if (dragState.value.resizeType === 'end') {
      const newDuration = Math.max(0.1, dragState.value.startTime - clip.start + deltaTime)
      updates.duration = newDuration
    }
    
    if (Object.keys(updates).length > 0) {
      emit('clipResized', props.rushId, dragState.value.draggedClipIndex, updates)
    }
  }
  
  // TODO: Implement clip dragging/reordering
}

const handleMouseUp = () => {
  dragState.value = {
    isDragging: false,
    isResizing: false,
    resizeType: null,
    draggedClipIndex: null,
    startX: 0,
    startTime: 0
  }
  
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped>
.timeline-track {
  display: flex;
  border-bottom: 1px solid #dee2e6;
  min-height: 80px;
}

.track-header {
  flex: 0 0 200px;
  padding: 12px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.track-content {
  flex: 1;
  position: relative;
  height: 80px;
  background: #fff;
  overflow: hidden;
}

.clip {
  position: absolute;
  top: 8px;
  height: 64px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  border: 2px solid #0056b3;
  border-radius: 4px;
  cursor: move;
  transition: all 0.2s ease;
  min-width: 50px;
}

.clip:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.clip.selected {
  border-color: #ffc107;
  box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.5);
}

.clip.has-effects {
  border-top-color: #ffc107;
}

.clip.has-overlays {
  border-bottom-color: #17a2b8;
}

.clip-content {
  position: relative;
  height: 100%;
  padding: 6px 8px;
  color: white;
  font-size: 11px;
  overflow: hidden;
}

.clip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.clip-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.clip-score {
  font-size: 9px;
  padding: 2px 4px;
}

.clip-body {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: calc(100% - 20px);
}

.clip-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.effect-indicators,
.overlay-indicators {
  display: flex;
  gap: 2px;
}

.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: ew-resize;
  background: rgba(255, 255, 255, 0.3);
  opacity: 0;
  transition: opacity 0.2s;
}

.clip:hover .resize-handle {
  opacity: 1;
}

.resize-left {
  left: 0;
}

.resize-right {
  right: 0;
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #dc3545;
  pointer-events: none;
  z-index: 10;
}

.playhead::before {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  width: 10px;
  height: 10px;
  background: #dc3545;
  border-radius: 50%;
}
</style>