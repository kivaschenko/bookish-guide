<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
      <RouterLink to="/dashboard" class="navbar-brand">
        <i class="fas fa-video me-2"></i>
        StoryForge
      </RouterLink>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              id="navbarDropdown"
              role="button"
              data-bs-toggle="dropdown"
            >
              <i class="fas fa-user me-1"></i>
              {{ authStore.user?.username }}
            </a>
            <ul class="dropdown-menu">
              <li>
                <RouterLink to="/profile" class="dropdown-item">
                  <i class="fas fa-user-edit me-2"></i>
                  Profile
                </RouterLink>
              </li>
              <li><hr class="dropdown-divider" /></li>
              <li>
                <button @click="handleLogout" class="dropdown-item">
                  <i class="fas fa-sign-out-alt me-2"></i>
                  Logout
                </button>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const handleLogout = async () => {
  try {
    await authStore.logout()
    notificationStore.addNotification({
      message: 'Successfully logged out',
      type: 'success'
    })
    router.push('/login')
  } catch (error) {
    notificationStore.addNotification({
      message: 'Error during logout',
      type: 'error'
    })
  }
}
</script>