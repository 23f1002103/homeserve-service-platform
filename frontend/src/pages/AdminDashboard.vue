<script setup>
import { onMounted, ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const dashboard = ref(null)
const errorMessage = ref('')

async function loadDashboard() {
  try {
    const response = await fetch('/api/admin/dashboard', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    if (!response.ok) throw new Error('Could not load the dashboard')
    dashboard.value = await response.json()
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="overview" />
    <main class="workbench-content">
      <section class="admin-intro">
        <div><p class="workbench-label">CONTROL ROOM / {{ new Date().getFullYear() }}</p><h1>Make every service<br />feel effortless.</h1></div>
        <p>Welcome, {{ user.username || 'Admin' }}. This overview shows the current health of HomeServe.</p>
      </section>

      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <section v-if="dashboard" class="admin-metrics" aria-label="Platform totals">
        <article><span>01</span><small>Customers</small><strong>{{ dashboard.counts.customers }}</strong></article>
        <article><span>02</span><small>Professionals</small><strong>{{ dashboard.counts.professionals }}</strong></article>
        <article class="metric-highlight"><span>03</span><small>Waiting for approval</small><strong>{{ dashboard.counts.pending_professionals }}</strong></article>
        <article><span>04</span><small>Open requests</small><strong>{{ dashboard.counts.open_requests }}</strong></article>
      </section>
      <section v-else-if="!errorMessage" class="dashboard-loading">Reading live platform data…</section>

      <section v-if="dashboard" class="admin-revenue-strip">
        <div><p class="workbench-label">PLATFORM REVENUE</p><h2>HomeServe commission</h2><small>This is the platform's share from completed services—not the admin's personal income.</small></div>
        <div><small>REVENUE TODAY</small><strong>₹{{ dashboard.revenue.today }}</strong></div>
        <div><small>ALL-TIME REVENUE</small><strong>₹{{ dashboard.revenue.total }}</strong></div>
      </section>

      <div v-if="dashboard" class="admin-board">
        <section class="board-panel overview-links">
          <div class="board-heading"><div><p class="workbench-label">WORKSPACE</p><h2>Manage the platform</h2></div></div>
          <RouterLink to="/admin/professionals"><strong>Professional approvals</strong><span>Review applications →</span></RouterLink>
          <RouterLink to="/admin/customers"><strong>Customer directory</strong><span>View customer accounts →</span></RouterLink>
          <RouterLink to="/admin/services"><strong>Service catalogue</strong><span>Create service types →</span></RouterLink>
          <RouterLink to="/admin/requests"><strong>Service requests</strong><span>Track bookings →</span></RouterLink>
          <RouterLink to="/admin/revenue"><strong>Revenue reports</strong><span>Review platform income →</span></RouterLink>
        </section>

        <section class="board-panel pulse-panel">
          <div class="board-heading"><div><p class="workbench-label">REQUEST PULSE</p><h2>Work in motion</h2></div></div>
          <div class="request-pulse">
            <div><span>Pending</span><strong>{{ dashboard.requests.pending }}</strong></div>
            <div><span>Accepted</span><strong>{{ dashboard.requests.accepted }}</strong></div>
            <div><span>Completed</span><strong>{{ dashboard.requests.completed }}</strong></div>
          </div>
          <p class="pulse-note">These totals come directly from PostgreSQL.</p>
        </section>
      </div>
    </main>
  </div>
</template>
