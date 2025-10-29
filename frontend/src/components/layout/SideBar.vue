<template>
  <nav class="sidebar">
    <div class="p-3">
      <ul class="nav nav-pills flex-column">
        <li class="nav-item">
          <RouterLink to="/dashboard" class="nav-link" active-class="active">
            <i class="fas fa-tachometer-alt me-2"></i>
            Dashboard
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink to="/projects" class="nav-link" active-class="active">
            <i class="fas fa-folder me-2"></i>
            Projects
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink to="/projects/new" class="nav-link" active-class="active">
            <i class="fas fa-plus me-2"></i>
            New Project
          </RouterLink>
        </li>
        <li class="nav-item mt-3">
          <h6 class="text-muted small text-uppercase">Tools</h6>
        </li>
        <li class="nav-item">
          <a href="#" class="nav-link">
            <i class="fas fa-images me-2"></i>
            B-roll Library
          </a>
        </li>
        <li class="nav-item">
          <a href="#" class="nav-link">
            <i class="fas fa-cog me-2"></i>
            Settings
          </a>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.sidebar {
  background-color: var(--dark-color);
  min-height: 100vh;
}

.sidebar h6 {
  padding: 0.5rem 0.75rem;
  margin: 0;
}

.nav-link {
  color: #d1d5db;
  border-radius: 0.375rem;
  margin-bottom: 0.25rem;
  transition: all 0.2s;
}

.nav-link:hover,
.nav-link.active {
  background-color: var(--primary-color);
  color: white;
}
</style>