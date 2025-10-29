<template>
  <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 9999">
    <div
      v-for="notification in notificationStore.notifications"
      :key="notification.id"
      class="toast show"
      role="alert"
    >
      <div class="toast-header" :class="getHeaderClass(notification.type)">
        <i :class="getIconClass(notification.type)" class="me-2"></i>
        <strong class="me-auto">{{ getTitle(notification.type) }}</strong>
        <button
          type="button"
          class="btn-close"
          @click="notificationStore.removeNotification(notification.id)"
        ></button>
      </div>
      <div class="toast-body">
        {{ notification.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

const getHeaderClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'bg-success text-white'
    case 'error':
      return 'bg-danger text-white'
    case 'warning':
      return 'bg-warning text-dark'
    case 'info':
      return 'bg-info text-white'
    default:
      return 'bg-primary text-white'
  }
}

const getIconClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'fas fa-check-circle'
    case 'error':
      return 'fas fa-exclamation-circle'
    case 'warning':
      return 'fas fa-exclamation-triangle'
    case 'info':
      return 'fas fa-info-circle'
    default:
      return 'fas fa-bell'
  }
}

const getTitle = (type: string) => {
  switch (type) {
    case 'success':
      return 'Success'
    case 'error':
      return 'Error'
    case 'warning':
      return 'Warning'
    case 'info':
      return 'Information'
    default:
      return 'Notification'
  }
}
</script>

<style scoped>
.toast {
  margin-bottom: 0.5rem;
}
</style>