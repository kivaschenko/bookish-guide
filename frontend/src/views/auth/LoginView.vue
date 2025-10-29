<template>
  <div class="min-vh-100 d-flex align-items-center bg-light">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
          <div class="card shadow">
            <div class="card-body p-5">
              <div class="text-center mb-4">
                <h2 class="fw-bold text-primary">
                  <i class="fas fa-video me-2"></i>
                  StoryForge
                </h2>
                <p class="text-muted">Sign in to your account</p>
              </div>

              <form @submit.prevent="handleLogin">
                <div class="form-floating mb-3">
                  <input
                    v-model="form.username"
                    type="text"
                    class="form-control"
                    id="username"
                    placeholder="Username"
                    required
                  />
                  <label for="username">Username</label>
                </div>

                <div class="form-floating mb-4">
                  <input
                    v-model="form.password"
                    type="password"
                    class="form-control"
                    id="password"
                    placeholder="Password"
                    required
                  />
                  <label for="password">Password</label>
                </div>

                <div class="d-grid">
                  <button
                    type="submit"
                    class="btn btn-primary btn-lg"
                    :disabled="authStore.isLoading"
                  >
                    <span
                      v-if="authStore.isLoading"
                      class="spinner-border spinner-border-sm me-2"
                    ></span>
                    Sign In
                  </button>
                </div>

                <div v-if="authStore.error" class="alert alert-danger mt-3">
                  {{ authStore.error }}
                </div>
              </form>

              <div class="text-center mt-4">
                <p class="text-muted">
                  Don't have an account?
                  <RouterLink to="/register" class="text-decoration-none">
                    Sign up
                  </RouterLink>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  const success = await authStore.login(form.value)
  if (success) {
    notificationStore.addNotification({
      message: 'Successfully logged in!',
      type: 'success'
    })
    router.push('/dashboard')
  }
}

onMounted(() => {
  authStore.clearError()
})
</script>