import { createRouter, createWebHistory } from 'vue-router'

import LandingPage from '../pages/LandingPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import RegisterPage from '../pages/RegisterPage.vue'
import AdminDashboard from '../pages/AdminDashboard.vue'
import AdminProfessionalsPage from '../pages/AdminProfessionalsPage.vue'
import AdminCustomersPage from '../pages/AdminCustomersPage.vue'
import AdminServicesPage from '../pages/AdminServicesPage.vue'
import AdminServiceAreasPage from '../pages/AdminServiceAreasPage.vue'
import AdminRequestsPage from '../pages/AdminRequestsPage.vue'
import AdminRevenuePage from '../pages/AdminRevenuePage.vue'
import CustomerDashboard from '../pages/CustomerDashboard.vue'
import CustomerServicesPage from '../pages/CustomerServicesPage.vue'
import CustomerBookingsPage from '../pages/CustomerBookingsPage.vue'
import CustomerBookingPage from '../pages/CustomerBookingPage.vue'
import CustomerProfilePage from '../pages/CustomerProfilePage.vue'
import ProfessionalDashboard from '../pages/ProfessionalDashboard.vue'
import ProfessionalJobsPage from '../pages/ProfessionalJobsPage.vue'
import ProfessionalProfilePage from '../pages/ProfessionalProfilePage.vue'
import ProfessionalEarningsPage from '../pages/ProfessionalEarningsPage.vue'
import ProfessionalServiceAreasPage from '../pages/ProfessionalServiceAreasPage.vue'
import ProfessionalPendingPage from '../pages/ProfessionalPendingPage.vue'
import ProfessionalBlockedPage from '../pages/ProfessionalBlockedPage.vue'


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: LandingPage },
    { path: '/login', name: 'login', component: LoginPage },
    { path: '/register', name: 'register', component: RegisterPage },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/professionals',
      name: 'admin-professionals',
      component: AdminProfessionalsPage,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/customers',
      name: 'admin-customers',
      component: AdminCustomersPage,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/services',
      name: 'admin-services',
      component: AdminServicesPage,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/service-areas',
      name: 'admin-service-areas',
      component: AdminServiceAreasPage,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/requests',
      name: 'admin-requests',
      component: AdminRequestsPage,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/revenue',
      name: 'admin-revenue',
      component: AdminRevenuePage,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/customer/dashboard',
      name: 'customer-dashboard',
      component: CustomerDashboard,
      meta: { requiresAuth: true, role: 'customer' },
    },
    {
      path: '/customer/services',
      name: 'customer-services',
      component: CustomerServicesPage,
      meta: { requiresAuth: true, role: 'customer' },
    },
    {
      path: '/customer/bookings',
      name: 'customer-bookings',
      component: CustomerBookingsPage,
      meta: { requiresAuth: true, role: 'customer' },
    },
    {
      path: '/customer/book/:serviceId',
      name: 'customer-book-service',
      component: CustomerBookingPage,
      meta: { requiresAuth: true, role: 'customer' },
    },
    {
      path: '/customer/profile',
      name: 'customer-profile',
      component: CustomerProfilePage,
      meta: { requiresAuth: true, role: 'customer' },
    },
    {
      path: '/professional/dashboard',
      name: 'professional-dashboard',
      component: ProfessionalDashboard,
      meta: { requiresAuth: true, role: 'professional' },
    },
    {
      path: '/professional/jobs',
      name: 'professional-jobs',
      component: ProfessionalJobsPage,
      meta: { requiresAuth: true, role: 'professional' },
    },
    {
      path: '/professional/profile',
      name: 'professional-profile',
      component: ProfessionalProfilePage,
      meta: { requiresAuth: true, role: 'professional' },
    },
    {
      path: '/professional/earnings',
      name: 'professional-earnings',
      component: ProfessionalEarningsPage,
      meta: { requiresAuth: true, role: 'professional' },
    },
    {
      path: '/professional/service-areas',
      name: 'professional-service-areas',
      component: ProfessionalServiceAreasPage,
      meta: { requiresAuth: true, role: 'professional' },
    },
    {
      path: '/professional/pending',
      name: 'professional-pending',
      component: ProfessionalPendingPage,
      meta: { requiresAuth: true, role: 'professional' },
    },
    {
      path: '/professional/blocked',
      name: 'professional-blocked',
      component: ProfessionalBlockedPage,
      meta: { requiresAuth: true, role: 'professional' },
    },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.requiresAuth) return true

  const token = localStorage.getItem('access_token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  if (!token) return '/login'
  if (to.meta.role && user.role !== to.meta.role) return '/'

  return true
})

export default router

