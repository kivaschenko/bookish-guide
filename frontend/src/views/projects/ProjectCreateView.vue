<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 fw-bold">Create New Project</h1>
    <RouterLink to="/projects" class="btn btn-outline-secondary">
      <i class="fas fa-arrow-left me-2"></i>
      Back to Projects
    </RouterLink>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card">
        <div class="card-body">
          <form @submit.prevent="handleSubmit">
            <div class="row">
              <div class="col-md-8">
                <div class="form-floating mb-3">
                  <input
                    v-model="form.name"
                    type="text"
                    class="form-control"
                    id="projectName"
                    placeholder="Project Name"
                    required
                    maxlength="255"
                  />
                  <label for="projectName">Project Name</label>
                </div>
              </div>
              <div class="col-md-4">
                <div class="form-floating mb-3">
                  <select v-model="form.language" class="form-select" id="language">
                    <option value="english">English</option>
                    <option value="spanish">Spanish</option>
                    <option value="french">French</option>
                    <option value="german">German</option>
                    <option value="italian">Italian</option>
                  </select>
                  <label for="language">Language</label>
                </div>
              </div>
            </div>

            <div class="form-floating mb-3">
              <textarea
                v-model="form.description"
                class="form-control"
                id="description"
                style="height: 100px"
                placeholder="Project Description"
                maxlength="1000"
              ></textarea>
              <label for="description">Description (Optional)</label>
            </div>

            <div class="form-floating mb-4">
              <textarea
                v-model="form.input_text"
                class="form-control"
                id="inputText"
                style="height: 200px"
                placeholder="Enter your video content, ideas, or script here..."
                required
              ></textarea>
              <label for="inputText">Content / Script</label>
              <div class="form-text">
                Enter the text content that will be used to generate your video script and voice-over.
              </div>
            </div>

            <div class="d-flex justify-content-between">
              <RouterLink to="/projects" class="btn btn-secondary">
                Cancel
              </RouterLink>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="projectStore.isLoading"
              >
                <span
                  v-if="projectStore.isLoading"
                  class="spinner-border spinner-border-sm me-2"
                ></span>
                Create Project
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-info-circle me-2"></i>
            Project Tips
          </h5>
        </div>
        <div class="card-body">
          <div class="mb-3">
            <h6 class="fw-bold">Content Guidelines</h6>
            <ul class="small text-muted">
              <li>Write clear, engaging content</li>
              <li>Use bullet points for better structure</li>
              <li>Keep sentences conversational</li>
              <li>Aim for 50-500 words per minute of video</li>
            </ul>
          </div>

          <div class="mb-3">
            <h6 class="fw-bold">Languages Supported</h6>
            <p class="small text-muted">
              Currently supporting English, Spanish, French, German, and Italian
              for voice synthesis and script generation.
            </p>
          </div>

          <div>
            <h6 class="fw-bold">Next Steps</h6>
            <p class="small text-muted">
              After creating your project, you can generate the script,
              add voice-over, and synchronize B-roll footage.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const projectStore = useProjectStore()
const notificationStore = useNotificationStore()

const form = ref({
  name: '',
  description: '',
  input_text: '',
  language: 'english'
})

const handleSubmit = async () => {
  try {
    const project = await projectStore.createProject({
      name: form.value.name,
      description: form.value.description || undefined,
      input_text: form.value.input_text || undefined,
      language: form.value.language
    })

    notificationStore.addNotification({
      message: `Project "${project.name}" created successfully!`,
      type: 'success'
    })

    router.push(`/projects/${project.id}/edit`)
  } catch (error) {
    notificationStore.addNotification({
      message: 'Failed to create project',
      type: 'error'
    })
  }
}
</script>