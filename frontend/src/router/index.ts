import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Views
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ProjectsView from '@/views/projects/ProjectsView.vue'
import ProjectCreateView from '@/views/projects/ProjectCreateView.vue'
import ProjectEditView from '@/views/projects/ProjectEditView.vue'
import ProjectTimelineView from '@/views/projects/ProjectTimelineView.vue'
import BRollView from '@/views/broll/BRollView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresGuest: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }
    },
    {
      path: '/projects',
      name: 'projects',
      component: ProjectsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/projects/new',
      name: 'project-create',
      component: ProjectCreateView,
      meta: { requiresAuth: true }
    },
    {
      path: '/projects/:id/edit',
      name: 'project-edit',
      component: ProjectEditView,
      meta: { requiresAuth: true },
      props: true
    },
    {
      path: '/projects/:id/timeline',
      name: 'project-timeline',
      component: ProjectTimelineView,
      meta: { requiresAuth: true },
      props: true
    },
    {
      path: '/broll',
      name: 'broll',
      component: BRollView,
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guards
router.beforeEach(async (to: any, from: any, next: any) => {
  const authStore = useAuthStore()
  
  // If user has token but no user data, try to load user data
  if (authStore.token && !authStore.user) {
    try {
      await authStore.checkAuth()
    } catch (error) {
      console.error('Auth check failed:', error)
    }
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router