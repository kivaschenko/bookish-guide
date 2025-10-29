import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { 
  BRoll, 
  BRollUploadData, 
  BRollUpdateData, 
  BRollListResponse, 
  BRollFilters,
  StorageStats 
} from '@/services/brollApi'
import { brollApi } from '@/services/brollApi'

export const useBRollStore = defineStore('broll', () => {
  // State
  const brolls = ref<BRoll[]>([])
  const currentBRoll = ref<BRoll | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const uploadProgress = ref(0)
  const storageStats = ref<StorageStats | null>(null)

  // Pagination state
  const currentPage = ref(1)
  const totalPages = ref(0)
  const totalItems = ref(0)
  const perPage = ref(20)

  // Filter state
  const filters = ref<BRollFilters>({
    page: 1,
    per_page: 20,
  })

  // Actions
  const setError = (message: string) => {
    error.value = message
  }

  const clearError = () => {
    error.value = null
  }

  const fetchBRolls = async (newFilters?: BRollFilters): Promise<BRollListResponse> => {
    try {
      isLoading.value = true
      clearError()

      // Update filters if provided
      if (newFilters) {
        filters.value = { ...filters.value, ...newFilters }
      }

      const response = await brollApi.listBRoll(filters.value)
      
      brolls.value = response.brolls
      currentPage.value = response.page
      totalPages.value = response.total_pages
      totalItems.value = response.total
      perPage.value = response.per_page

      return response
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch B-roll items'
      setError(message)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchBRoll = async (id: number): Promise<BRoll> => {
    try {
      isLoading.value = true
      clearError()

      const broll = await brollApi.getBRoll(id)
      currentBRoll.value = broll

      return broll
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch B-roll item'
      setError(message)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const uploadBRoll = async (data: BRollUploadData) => {
    try {
      isLoading.value = true
      uploadProgress.value = 0
      clearError()

      const response = await brollApi.uploadBRoll(data)
      
      if (response.success && response.broll) {
        // Add to the beginning of the list
        brolls.value.unshift(response.broll)
        totalItems.value += 1
      }

      uploadProgress.value = 100
      return response
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to upload B-roll'
      setError(message)
      throw err
    } finally {
      isLoading.value = false
      uploadProgress.value = 0
    }
  }

  const updateBRoll = async (id: number, data: BRollUpdateData): Promise<BRoll> => {
    try {
      isLoading.value = true
      clearError()

      const updatedBRoll = await brollApi.updateBRoll(id, data)
      
      // Update in the list
      const index = brolls.value.findIndex(b => b.id === id)
      if (index !== -1) {
        brolls.value[index] = updatedBRoll
      }

      // Update current if it's the same
      if (currentBRoll.value?.id === id) {
        currentBRoll.value = updatedBRoll
      }

      return updatedBRoll
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to update B-roll'
      setError(message)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteBRoll = async (id: number, permanent: boolean = false) => {
    try {
      isLoading.value = true
      clearError()

      await brollApi.deleteBRoll(id, permanent)
      
      // Remove from list if permanently deleted, or refetch if soft deleted
      if (permanent) {
        brolls.value = brolls.value.filter(b => b.id !== id)
        totalItems.value -= 1
      } else {
        // Refresh the list to show updated status
        await fetchBRolls()
      }

      // Clear current if it's the same
      if (currentBRoll.value?.id === id) {
        currentBRoll.value = null
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to delete B-roll'
      setError(message)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchStorageStats = async (): Promise<StorageStats> => {
    try {
      clearError()

      const stats = await brollApi.getStorageStats()
      storageStats.value = stats

      return stats
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch storage stats'
      setError(message)
      throw err
    }
  }

  const setFilters = (newFilters: BRollFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const clearFilters = () => {
    filters.value = {
      page: 1,
      per_page: 20,
    }
  }

  const searchBRolls = async (query: string) => {
    await fetchBRolls({
      ...filters.value,
      search: query,
      page: 1 // Reset to first page when searching
    })
  }

  const filterByCategory = async (category: string) => {
    await fetchBRolls({
      ...filters.value,
      category,
      page: 1 // Reset to first page when filtering
    })
  }

  const filterByTags = async (tags: string) => {
    await fetchBRolls({
      ...filters.value,
      tags,
      page: 1 // Reset to first page when filtering
    })
  }

  const changePage = async (page: number) => {
    await fetchBRolls({
      ...filters.value,
      page
    })
  }

  const getFileUrl = (filename: string): string => {
    return brollApi.getFileUrl(filename)
  }

  return {
    // State
    brolls,
    currentBRoll,
    isLoading,
    error,
    uploadProgress,
    storageStats,
    currentPage,
    totalPages,
    totalItems,
    perPage,
    filters,

    // Actions
    setError,
    clearError,
    fetchBRolls,
    fetchBRoll,
    uploadBRoll,
    updateBRoll,
    deleteBRoll,
    fetchStorageStats,
    setFilters,
    clearFilters,
    searchBRolls,
    filterByCategory,
    filterByTags,
    changePage,
    getFileUrl,
  }
})