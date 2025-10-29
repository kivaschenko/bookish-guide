<template>
  <div id="app">
    <NavBar v-if="authStore.isAuthenticated" />
    <div class="container-fluid" v-if="authStore.isAuthenticated">
      <div class="row">
        <SideBar class="col-md-3 col-lg-2 px-0" />
        <main class="col-md-9 col-lg-10 px-md-4">
          <RouterView />
        </main>
      </div>
    </div>
    <div v-else>
      <RouterView />
    </div>
    
    <!-- Global notifications -->
    <NotificationToast />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'
import NavBar from './components/layout/NavBar.vue'
import SideBar from './components/layout/SideBar.vue'
import NotificationToast from './components/common/NotificationToast.vue'

const authStore = useAuthStore()

onMounted(() => {
  // Check for existing authentication on app startup
  authStore.checkAuth()
})
</script>

<style scoped>
#app {
  min-height: 100vh;
}

main {
  padding-top: 1.5rem;
}
</style>