<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const dashboard = ref(null)
const errorMessage = ref('')
const formatDate = (value) => value
  ? new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  : 'Not scheduled'

async function loadDashboard() {
  try {
    const response = await fetch('/api/professional/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load your dashboard')
    if (data.approval_status === 'pending') return router.replace('/professional/pending')
    if (data.approval_status === 'blocked') return router.replace('/professional/blocked')
    if (data.service_area_count === 0) return router.replace('/professional/location')
    dashboard.value = data
  } catch (error) { errorMessage.value = error.message }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="workbench professional-workbench">
    <ProfessionalHeader current="overview" />
    <main class="workbench-content professional-content">
      <section class="professional-intro">
        <div><p class="workbench-label">FIELD DESK / {{ user.username || 'PROFESSIONAL' }}</p><h1>Good work starts<br />with a clear plan.</h1></div>
        <div class="shift-stamp"><small>ACCOUNT STATUS</small><strong>{{ dashboard ? 'READY FOR WORK' : 'CHECKING' }}</strong><span></span></div>
      </section>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <div v-else-if="!dashboard" class="dashboard-loading">Preparing your field desk…</div>
      <template v-else>
        <section class="professional-summary">
          <article class="trade-card"><span>YOUR TRADE</span><strong>{{ dashboard.service }}</strong><small>{{ dashboard.city }}</small></article>
          <article><span>ACTIVE JOBS</span><strong>{{ dashboard.accepted_jobs }}</strong><small>Accepted requests</small></article>
          <article><span>WORK COMPLETED</span><strong>{{ dashboard.completed_jobs }}</strong><small>Finished requests</small></article>
          <article class="earning-card"><span>TODAY'S EARNINGS</span><strong>₹{{ dashboard.today_earning }}</strong><small>Your share from completed work</small></article>
        </section>
        <section class="dashboard-available-work">
          <header>
            <div><p class="workbench-label">AVAILABLE IN YOUR AREA</p><h2>Bookings ready for you.</h2></div>
            <RouterLink to="/professional/jobs">View all {{ dashboard.available_job_count }} →</RouterLink>
          </header>
          <div v-if="dashboard.available_jobs.length" class="available-job-list dashboard-job-preview">
            <article v-for="job in dashboard.available_jobs" :key="job.id">
              <header><code>#{{ String(job.id).padStart(4, '0') }}</code><span>{{ job.area }}</span></header>
              <div><p class="workbench-label">{{ job.service }}</p><h2>{{ job.description }}</h2></div>
              <footer><time>{{ formatDate(job.scheduled_for) }}</time><strong>{{ job.price ? `₹${job.price}` : 'Price unavailable' }}</strong><RouterLink to="/professional/jobs">Open job</RouterLink></footer>
            </article>
          </div>
          <div v-else class="empty-job-sheet"><span></span><div><h3>No matching requests right now.</h3><p>New paid bookings matching your trade and saved service area will appear here.</p></div></div>
        </section>
        <section class="role-page-links">
          <RouterLink to="/professional/jobs"><span>01</span><div><strong>My jobs</strong><small>View assignments and schedules</small></div><b>→</b></RouterLink>
          <RouterLink to="/professional/service-areas"><span>02</span><div><strong>Service areas</strong><small>{{ dashboard.service_area_count }} areas assigned</small></div><b>→</b></RouterLink>
          <RouterLink to="/professional/earnings"><span>03</span><div><strong>Weekly earnings</strong><small>Choose a week and view its payout</small></div><b>→</b></RouterLink>
        </section>
      </template>
    </main>
  </div>
</template>
