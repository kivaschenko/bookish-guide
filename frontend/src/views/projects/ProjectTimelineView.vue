<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">Project Timeline</h1>
    <RouterLink :to="`/projects/${projectId}/edit`" class="btn btn-outline-secondary">
      <i class="fas fa-arrow-left me-2"></i>
      Back to Project
    </RouterLink>
  </div>

  <div v-if="projectStore.isLoading || timelineStore.state.isLoading" class="text-center py-4">
    <div class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>

  <div v-else-if="!project" class="alert alert-danger">
    Project not found.
  </div>

  <div v-else>
    <!-- Timeline Controls -->
    <TimelineControls @zoom-changed="handleZoomChange" class="mb-4" />

    <!-- Main Timeline Editor -->
    <div class="timeline-editor-container">
      <div class="row">
        <!-- Timeline Tracks -->
        <div class="col-lg-8">
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">
                <i class="fas fa-film me-2"></i>
                Video Timeline
              </h6>
            </div>
            <div class="card-body p-0">
              <div v-if="!timelineStore.state.timeline" class="text-center py-5">
                <i class="fas fa-film fa-3x text-muted mb-3"></i>
                <p class="text-muted mb-3">No timeline data available</p>
                <button 
                  class="btn btn-primary"
                  @click="loadTimelineData"
                  :disabled="timelineStore.state.isLoading"
                >
                  <span v-if="timelineStore.state.isLoading" class="spinner-border spinner-border-sm me-2"></span>
                  Load Timeline
                </button>
              </div>
              
              <div v-else class="timeline-container">
                <!-- Timeline Header -->
                <div class="timeline-header">
                  <div class="track-labels">
                    <div class="time-ruler">
                      <div 
                        v-for="mark in timeMarks" 
                        :key="mark.time"
                        class="time-mark"
                        :style="{ left: `${mark.position}px` }"
                      >
                        <span class="time-label">{{ formatTime(mark.time) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Timeline Tracks -->
                <div class="timeline-tracks" ref="tracksContainer">
                  <TimelineTrack
                    v-for="(rush, rushId) in timelineStore.rushes"
                    :key="rushId"
                    :rush-id="rushId"
                    :rush="rush"
                    :timeline-width="timelineWidth"
                    :pixels-per-second="pixelsPerSecond"
                    :current-time="timelineStore.state.currentTime"
                    :show-playhead="true"
                    @clip-selected="handleClipSelected"
                    @clip-moved="handleClipMoved"
                    @clip-resized="handleClipResized"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Clip Editor Sidebar -->
        <div class="col-lg-4">
          <div class="sticky-top" style="top: 20px;">
            <!-- Project Status -->
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

            <!-- Clip Editor -->
            <div v-if="timelineStore.state.selectedClip" class="card mb-3">
              <ClipEditor
                :rush-id="timelineStore.state.selectedClip.rushId"
                :clip-index="timelineStore.state.selectedClip.clipIndex"
              />
            </div>

            <!-- B-roll Library Tool -->
            <div class="card mb-3">
              <div class="card-header">
                <h6 class="mb-0">B-roll Library</h6>
              </div>
              <div class="card-body">
                <div class="d-grid gap-2">
                  <button 
                    class="btn btn-outline-primary"
                    @click="openBrollLibrary"
                  >
                    <i class="fas fa-images me-2"></i>
                    Browse B-roll
                  </button>
                  <button 
                    class="btn btn-outline-success"
                    @click="uploadBroll"
                  >
                    <i class="fas fa-upload me-2"></i>
                    Upload New
                  </button>
                </div>
              </div>
            </div>

            <!-- Quick Tools -->
            <div class="card">
              <div class="card-header">
                <h6 class="mb-0">Quick Tools</h6>
              </div>
              <div class="card-body">
                <div class="d-grid gap-2">
                  <button 
                    class="btn btn-outline-info"
                    @click="autoSyncAudio"
                    :disabled="!timelineStore.state.timeline"
                  >
                    <i class="fas fa-music me-2"></i>
                    Auto-sync Audio
                  </button>
                  <button 
                    class="btn btn-outline-warning"
                    @click="applyBulkEffects"
                    :disabled="!timelineStore.state.timeline"
                  >
                    <i class="fas fa-palette me-2"></i>
                    Bulk Effects
                  </button>
                  <button 
                    class="btn btn-outline-danger"
                    @click="resetTimeline"
                    :disabled="!timelineStore.state.timeline"
                  >
                    <i class="fas fa-undo me-2"></i>
                    Reset Timeline
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
import { useTimelineStore } from '@/stores/timeline'
import { useNotificationStore } from '@/stores/notification'
import type { Project } from '@/types/project'
import type { BrollClip } from '@/services/timelineApi'

// Import components
import TimelineControls from '@/components/timeline/TimelineControls.vue'
import TimelineTrack from '@/components/timeline/TimelineTrack.vue' 
import ClipEditor from '@/components/timeline/ClipEditor.vue'

const route = useRoute()
const projectStore = useProjectStore()
const timelineStore = useTimelineStore()
const notificationStore = useNotificationStore()

const projectId = computed(() => parseInt(route.params.id as string))
const project = ref<Project | null>(null)
const tracksContainer = ref<HTMLElement>()

// Timeline display settings
const zoomLevel = ref(1)
const basePixelsPerSecond = ref(50)
const timelineWidth = computed(() => {
  return Math.max(800, timelineStore.totalTimelineDuration * pixelsPerSecond.value)
})
const pixelsPerSecond = computed(() => basePixelsPerSecond.value * zoomLevel.value)

// Time ruler marks
const timeMarks = computed(() => {
  const marks = []
  const duration = timelineStore.totalTimelineDuration
  const interval = duration > 60 ? 10 : duration > 30 ? 5 : 1
  
  for (let time = 0; time <= duration; time += interval) {
    marks.push({
      time,
      position: time * pixelsPerSecond.value + 200 // Offset for track labels
    })
  }
  return marks
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

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
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

const loadTimelineData = async () => {
  try {
    await timelineStore.loadTimeline()
    notificationStore.addNotification({
      message: 'Timeline loaded successfully',
      type: 'success'
    })
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to load timeline data. Make sure B-roll processing is completed.',
      type: 'error'
    })
  }
}

const handleZoomChange = (newZoom: number) => {
  zoomLevel.value = newZoom
}

const handleClipSelected = (rushId: string, clipIndex: number) => {
  timelineStore.selectClip(rushId, clipIndex)
}

const handleClipMoved = (rushId: string, fromIndex: number, toIndex: number) => {
  timelineStore.reorderClips(rushId, fromIndex, toIndex)
  notificationStore.addNotification({
    message: 'Clip reordered',
    type: 'success'
  })
}

const handleClipResized = (rushId: string, clipIndex: number, updates: Partial<BrollClip>) => {
  timelineStore.updateClipTiming(rushId, clipIndex, updates)
}

const openBrollLibrary = () => {
  // TODO: Open B-roll library modal/page
  notificationStore.addNotification({
    message: 'B-roll library coming soon!',
    type: 'info'
  })
}

const uploadBroll = () => {
  // TODO: Open B-roll upload modal
  notificationStore.addNotification({
    message: 'B-roll upload coming soon!',
    type: 'info'
  })
}

const autoSyncAudio = () => {
  notificationStore.addNotification({
    message: 'Auto-sync audio feature coming soon!',
    type: 'info'
  })
}

const applyBulkEffects = () => {
  notificationStore.addNotification({
    message: 'Bulk effects feature coming soon!',
    type: 'info'
  })
}

const resetTimeline = async () => {
  if (confirm('Are you sure you want to reset the timeline? This action cannot be undone.')) {
    try {
      await loadTimelineData()
      timelineStore.selectRush('')
      notificationStore.addNotification({
        message: 'Timeline reset successfully',
        type: 'success'
      })
    } catch (error) {
      notificationStore.addNotification({
        message: 'Failed to reset timeline',
        type: 'error'
      })
    }
  }
}

onMounted(async () => {
  await loadProject()
  
  // Auto-load timeline if project is completed
  if (project.value?.status === 'completed') {
    await loadTimelineData()
  }
})
</script>

<style scoped>
.timeline-editor-container {
  min-height: 600px;
}

.timeline-container {
  position: relative;
  overflow-x: auto;
  overflow-y: hidden;
  border: 1px solid #dee2e6;
  border-radius: 0 0 0.375rem 0.375rem;
}

.timeline-header {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  height: 40px;
}

.track-labels {
  position: relative;
  height: 40px;
}

.time-ruler {
  position: relative;
  height: 100%;
  background: linear-gradient(to right, transparent 199px, #dee2e6 200px);
}

.time-mark {
  position: absolute;
  top: 0;
  height: 100%;
  border-left: 1px solid #adb5bd;
  padding-left: 4px;
  display: flex;
  align-items: center;
}

.time-label {
  font-size: 11px;
  font-weight: 500;
  color: #6c757d;
  background: #f8f9fa;
  padding: 2px 4px;
  border-radius: 2px;
}

.timeline-tracks {
  position: relative;
  min-height: 400px;
  background: #fff;
}

/* Status badge styles */
.badge-completed {
  background-color: #28a745;
  color: white;
}

.badge-processing {
  background-color: #007bff;
  color: white;
}

.badge-draft {
  background-color: #6c757d;
  color: white;
}

.badge-error {
  background-color: #dc3545;
  color: white;
}

/* Responsive design */
@media (max-width: 1200px) {
  .timeline-editor-container .row {
    flex-direction: column;
  }
  
  .timeline-editor-container .col-lg-4 {
    order: -1;
    margin-bottom: 1rem;
  }
  
  .timeline-editor-container .col-lg-4 .sticky-top {
    position: static !important;
  }
}

@media (max-width: 768px) {
  .timeline-container {
    font-size: 0.875rem;
  }
  
  .time-ruler {
    background: linear-gradient(to right, transparent 149px, #dee2e6 150px);
  }
  
  .track-labels {
    min-width: 150px;
  }
}

/* Custom scrollbar for timeline */
.timeline-container::-webkit-scrollbar {
  height: 12px;
}

.timeline-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 6px;
}

.timeline-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 6px;
}

.timeline-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>