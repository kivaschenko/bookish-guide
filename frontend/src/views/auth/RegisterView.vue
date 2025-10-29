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
                <p class="text-muted">Create your account</p>
              </div>

              <form @submit.prevent="handleRegister">
                <div class="form-floating mb-3">
                  <input
                    v-model="form.username"
                    type="text"
                    class="form-control"
                    id="username"
                    placeholder="Username"
                    required
                    minlength="3"
                  />
                  <label for="username">Username</label>
                </div>

                <div class="form-floating mb-3">
                  <input
                    v-model="form.email"
                    type="email"
                    class="form-control"
                    id="email"
                    placeholder="Email"
                    required
                  />
                  <label for="email">Email</label>
                </div>

                <div class="form-floating mb-3">
                  <input
                    v-model="form.password"
                    type="password"
                    class="form-control"
                    id="password"
                    placeholder="Password"
                    required
                    minlength="6"
                  />
                  <label for="password">Password</label>
                </div>

                <div class="form-floating mb-4">
                  <input
                    v-model="form.confirmPassword"
                    type="password"
                    class="form-control"
                    id="confirmPassword"
                    placeholder="Confirm Password"
                    required
                    :class="{ 'is-invalid': form.password !== form.confirmPassword && form.confirmPassword.length > 0 }"
                  />
                  <label for="confirmPassword">Confirm Password</label>
                  <div v-if="form.password !== form.confirmPassword && form.confirmPassword.length > 0" 
                       class="invalid-feedback">
                    Passwords do not match
                  </div>
                </div>

                <div class="d-grid">
                  <button
                    type="submit"
                    class="btn btn-primary btn-lg"
                    :disabled="authStore.isLoading || form.password !== form.confirmPassword"
                  >
                    <span
                      v-if="authStore.isLoading"
                      class="spinner-border spinner-border-sm me-2"
                    ></span>
                    Sign Up
                  </button>
                </div>

                <div v-if="authStore.error" class="alert alert-danger mt-3">
                  {{ authStore.error }}
                </div>
              </form>

              <div class="text-center mt-4">
                <p class="text-muted">
                  Already have an account?
                  <RouterLink to="/login" class="text-decoration-none">
                    Sign in
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
  email: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  if (form.value.password !== form.value.confirmPassword) {
    notificationStore.addNotification({
      message: 'Passwords do not match',
      type: 'error'
    })
    return
  }

  const success = await authStore.register({
    username: form.value.username,
    email: form.value.email,
    password: form.value.password
  })
  
  if (success) {
    notificationStore.addNotification({
      message: 'Account created successfully!',
      type: 'success'
    })
    router.push('/dashboard')
  }
}

onMounted(() => {
  authStore.clearError()
})
</script>