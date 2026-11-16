<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'
import AvailableJobCard from '../components/AvailableJobCard.vue'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const dashboard = ref(null)
const errorMessage = ref('')
const currentHour = new Date().getHours()
const greeting = currentHour < 12 ? 'Good morning' : currentHour < 17 ? 'Good afternoon' : 'Good evening'
const displayName = user.username || 'Professional'
const todayLabel = new Intl.DateTimeFormat('en-IN', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
}).format(new Date())
async function loadDashboard() {
  try {
    const response = await fetch('/api/professional/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load your dashboard')
    if (data.approval_status === 'pending') return router.replace('/professional/pending')
    if (data.approval_status === 'blocked') return router.replace('/professional/blocked')
    if (!data.location_verified || !data.current_area) return router.replace('/professional/location')
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
        <div>
          <p class="workbench-label">{{ todayLabel }}</p>
          <h1>{{ greeting }}, <span>{{ displayName }}.</span></h1>
          <p class="professional-intro__copy">Here is today’s work, schedule and earnings at a glance.</p>
        </div>
      </section>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <div v-else-if="!dashboard" class="dashboard-loading">Preparing your field desk…</div>
      <template v-else>
        <section class="professional-current-area">
          <div class="professional-location-copy">
            <span class="professional-location-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg></span>
            <p><small>CURRENT WORK LOCATION</small><strong>{{ dashboard.current_area.city }}, {{ dashboard.current_area.state }}</strong></p>
          </div>
          <div class="professional-location-actions"><span><i></i> GPS verified</span><RouterLink to="/professional/location">Detect again</RouterLink></div>
        </section>
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
            <AvailableJobCard v-for="job in dashboard.available_jobs" :key="job.id" :job="job" preview />
          </div>
          <div v-else class="empty-job-sheet"><span></span><div><h3>No matching requests right now.</h3><p>New paid bookings matching your trade and current GPS city will appear here.</p></div></div>
        </section>
        <section class="role-page-links">
          <RouterLink to="/professional/jobs"><span>01</span><div><strong>My jobs</strong><small>View assignments and schedules</small></div><b>→</b></RouterLink>
          <RouterLink to="/professional/earnings"><span>02</span><div><strong>Weekly earnings</strong><small>Choose a week and view its payout</small></div><b>→</b></RouterLink>
        </section>
      </template>
    </main>
  </div>
</template>
