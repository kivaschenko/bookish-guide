import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { timelineApi, type TimelineData, type Rush, type BrollClip, type EffectConfig, type OverlayConfig } from '@/services/timelineApi'

export interface TimelineState {
  timeline: TimelineData | null
  selectedRush: string | null
  selectedClip: { rushId: string; clipIndex: number } | null
  isLoading: boolean
  isPlaying: boolean
  currentTime: number
  totalDuration: number
  effects: Record<string, EffectConfig[]>
  overlays: Record<string, OverlayConfig[]>
  isDirty: boolean
}

export const useTimelineStore = defineStore('timeline', () => {
  const state = ref<TimelineState>({
    timeline: null,
    selectedRush: null,
    selectedClip: null,
    isLoading: false,
    isPlaying: false,
    currentTime: 0,
    totalDuration: 0,
    effects: {},
    overlays: {},
    isDirty: false
  })

  // Getters
  const rushes = computed(() => state.value.timeline?.rushes || {})
  
  const rushList = computed(() => 
    Object.entries(rushes.value).map(([id, rush]) => ({ id, ...rush }))
  )

  const selectedRushData = computed(() => {
    if (!state.value.selectedRush) return null
    return rushes.value[state.value.selectedRush]
  })

  const selectedClipData = computed(() => {
    if (!state.value.selectedClip) return null
    const rush = rushes.value[state.value.selectedClip.rushId]
    if (!rush) return null
    return rush.brolls[state.value.selectedClip.clipIndex]
  })

  const totalTimelineDuration = computed(() => {
    return Object.values(rushes.value).reduce((total, rush) => total + rush.duration, 0)
  })

  // Actions
  async function loadTimeline() {
    state.value.isLoading = true
    try {
      const timeline = await timelineApi.getTimeline()
      state.value.timeline = timeline
      state.value.totalDuration = totalTimelineDuration.value
      state.value.isDirty = false
    } catch (error) {
      console.error('Failed to load timeline:', error)
      throw error
    } finally {
      state.value.isLoading = false
    }
  }

  async function saveTimeline() {
    if (!state.value.timeline) return
    
    try {
      await timelineApi.updateTimeline(state.value.timeline.rushes)
      state.value.isDirty = false
      return true
    } catch (error) {
      console.error('Failed to save timeline:', error)
      throw error
    }
  }

  function selectRush(rushId: string) {
    state.value.selectedRush = rushId
    state.value.selectedClip = null
  }

  function selectClip(rushId: string, clipIndex: number) {
    state.value.selectedRush = rushId
    state.value.selectedClip = { rushId, clipIndex }
  }

  function updateClipTiming(rushId: string, clipIndex: number, updates: Partial<BrollClip>) {
    if (!state.value.timeline) return
    
    const rush = state.value.timeline.rushes[rushId]
    if (!rush || !rush.brolls[clipIndex]) return

    Object.assign(rush.brolls[clipIndex], updates)
    state.value.isDirty = true
  }

  function updateRushDuration(rushId: string, duration: number) {
    if (!state.value.timeline) return
    
    const rush = state.value.timeline.rushes[rushId]
    if (!rush) return

    rush.duration = duration
    state.value.totalDuration = totalTimelineDuration.value
    state.value.isDirty = true
  }

  function reorderClips(rushId: string, fromIndex: number, toIndex: number) {
    if (!state.value.timeline) return
    
    const rush = state.value.timeline.rushes[rushId]
    if (!rush) return

    const clips = rush.brolls
    const [movedClip] = clips.splice(fromIndex, 1)
    clips.splice(toIndex, 0, movedClip)
    state.value.isDirty = true
  }

  function removeClip(rushId: string, clipIndex: number) {
    if (!state.value.timeline) return
    
    const rush = state.value.timeline.rushes[rushId]
    if (!rush) return

    rush.brolls.splice(clipIndex, 1)
    state.value.isDirty = true
  }

  function addEffect(rushId: string, clipIndex: number, effect: EffectConfig) {
    const key = `${rushId}-${clipIndex}`
    if (!state.value.effects[key]) {
      state.value.effects[key] = []
    }
    state.value.effects[key].push(effect)
    state.value.isDirty = true
  }

  function removeEffect(rushId: string, clipIndex: number, effectIndex: number) {
    const key = `${rushId}-${clipIndex}`
    if (!state.value.effects[key]) return
    
    state.value.effects[key].splice(effectIndex, 1)
    state.value.isDirty = true
  }

  function addOverlay(rushId: string, clipIndex: number, overlay: OverlayConfig) {
    const key = `${rushId}-${clipIndex}`
    if (!state.value.overlays[key]) {
      state.value.overlays[key] = []
    }
    state.value.overlays[key].push(overlay)
    state.value.isDirty = true
  }

  function removeOverlay(rushId: string, clipIndex: number, overlayIndex: number) {
    const key = `${rushId}-${clipIndex}`
    if (!state.value.overlays[key]) return
    
    state.value.overlays[key].splice(overlayIndex, 1)
    state.value.isDirty = true
  }

  async function uploadOverlayImage(file: File, brollIndex: number) {
    try {
      const result = await timelineApi.uploadOverlayImage(file, brollIndex)
      state.value.isDirty = true
      return result
    } catch (error) {
      console.error('Failed to upload overlay image:', error)
      throw error
    }
  }

  function setCurrentTime(time: number) {
    state.value.currentTime = Math.max(0, Math.min(time, state.value.totalDuration))
  }

  function togglePlayback() {
    state.value.isPlaying = !state.value.isPlaying
  }

  function pause() {
    state.value.isPlaying = false
  }

  function play() {
    state.value.isPlaying = true
  }

  function reset() {
    state.value.timeline = null
    state.value.selectedRush = null
    state.value.selectedClip = null
    state.value.isLoading = false
    state.value.isPlaying = false
    state.value.currentTime = 0
    state.value.totalDuration = 0
    state.value.effects = {}
    state.value.overlays = {}
    state.value.isDirty = false
  }

  return {
    // State
    state: computed(() => state.value),
    
    // Getters
    rushes,
    rushList,
    selectedRushData,
    selectedClipData,
    totalTimelineDuration,
    
    // Actions
    loadTimeline,
    saveTimeline,
    selectRush,
    selectClip,
    updateClipTiming,
    updateRushDuration,
    reorderClips,
    removeClip,
    addEffect,
    removeEffect,
    addOverlay,
    removeOverlay,
    uploadOverlayImage,
    setCurrentTime,
    togglePlayback,
    pause,
    play,
    reset
  }
})