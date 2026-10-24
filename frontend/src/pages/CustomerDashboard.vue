<script setup>
import { onMounted, ref } from 'vue'
import CustomerHeader from '../components/CustomerHeader.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const dashboard = ref(null)
const errorMessage = ref('')

async function loadDashboard() {
  try {
    const response = await fetch('/api/customer/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load your dashboard')
    dashboard.value = data
  } catch (error) { errorMessage.value = error.message }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="workbench customer-workbench">
    <CustomerHeader current="overview" />
    <main class="workbench-content customer-content">
      <section class="customer-hero compact-customer-hero">
        <div class="customer-hero__copy"><p class="workbench-label">WELCOME HOME, {{ user.username || 'CUSTOMER' }}</p><h1>What needs a little<br /><em>care</em> today?</h1><p>Choose a service and keep every home-care request organised.</p><RouterLink class="customer-primary-action" to="/customer/services">Browse services <span>↘</span></RouterLink></div>
        <div v-if="dashboard" class="customer-glance"><small>YOUR HOME DESK</small><strong>{{ dashboard.open_bookings }}</strong><span>open bookings</span><p>{{ dashboard.completed_bookings }} completed · {{ dashboard.city }}</p></div>
      </section>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <section class="role-page-links customer-page-links">
        <RouterLink to="/customer/services"><span>01</span><div><strong>Explore services</strong><small>Find the right help for your home</small></div><b>→</b></RouterLink>
        <RouterLink to="/customer/bookings"><span>02</span><div><strong>My bookings</strong><small>Track current and previous requests</small></div><b>→</b></RouterLink>
      </section>
    </main>
  </div>
</template>
