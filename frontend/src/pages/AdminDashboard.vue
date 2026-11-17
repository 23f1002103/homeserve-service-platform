<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AdminHeader from '../components/AdminHeader.vue'
import { redirectExpiredSession } from '../utils/auth'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const router = useRouter()
const dashboard = ref(null)
const errorMessage = ref('')
const loading = ref(false)

async function loadDashboard() {
  errorMessage.value = ''
  loading.value = true
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch('/api/admin/dashboard', {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      })
      if (response.status === 401) {
        loading.value = false
        await redirectExpiredSession(router)
        return
      }
      if (!response.ok) throw new Error('Could not load the dashboard')
      dashboard.value = await response.json()
      loading.value = false
      return
    } catch (error) {
      if (attempt === 0) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      } else {
        errorMessage.value = error.message
      }
    }
  }
  loading.value = false
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

      <div v-if="errorMessage" class="dashboard-alert dashboard-retry-alert"><span>{{ errorMessage }}</span><button type="button" :disabled="loading" @click="loadDashboard">{{ loading ? 'Retrying…' : 'Retry' }}</button></div>
      <section v-if="dashboard" class="admin-metrics" aria-label="Platform totals">
        <article><span>01</span><small>Customers</small><strong>{{ dashboard.counts.customers }}</strong></article>
        <article><span>02</span><small>Professionals</small><strong>{{ dashboard.counts.professionals }}</strong></article>
        <article class="metric-highlight"><span>03</span><small>Waiting for approval</small><strong>{{ dashboard.counts.pending_professionals }}</strong></article>
        <article><span>04</span><small>Open requests</small><strong>{{ dashboard.counts.open_requests }}</strong></article>
      </section>
      <section v-else-if="loading || !errorMessage" class="dashboard-loading">Reading live platform data…</section>

      <section v-if="dashboard" class="expansion-demand-panel">
        <header><div><p class="workbench-label">EXPANSION DEMAND</p><h2>Where HomeServe should operate next</h2><p>Customer interest is combined with professionals who registered from the same city and service.</p></div><RouterLink to="/admin/service-areas">Configure cities →</RouterLink></header>
        <div v-if="dashboard.expansion_demand.length" class="expansion-demand-list">
          <article v-for="item in dashboard.expansion_demand.slice(0, 8)" :key="`${item.state}-${item.city}-${item.service_type_id}`">
            <div><strong>{{ item.city }}, {{ item.state }}</strong><small>{{ item.service }}</small></div>
            <span><small>CUSTOMERS</small><strong>{{ item.customer_interest_count }}</strong></span>
            <span><small>PROFESSIONALS</small><strong>{{ item.professional_count }}</strong></span>
            <b>{{ item.city_supported ? 'Enable service' : 'New city opportunity' }}</b>
          </article>
        </div>
        <p v-else class="records-empty">No unsupported city or service demand has been recorded yet.</p>
      </section>

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
