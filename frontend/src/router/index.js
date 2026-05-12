import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/register',
    name: 'StudentRegister',
    component: () => import('../components/StudentRegister.vue')
  },
  {
    path: '/teacher/dashboard',
    name: 'TeacherDashboard',
    component: () => import('../views/teacher/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
  const userRole = localStorage.getItem('userRole')

  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      return '/login'
    } else if (to.meta.role && userRole !== to.meta.role) {
      if (userRole === 'teacher') {
        return '/teacher/dashboard'
      } else if (userRole === 'student') {
        return '/dashboard'
      } else {
        return '/login'
      }
    }
  }
})

export default router