<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import CustomerHeader from '../components/CustomerHeader.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const dashboard = ref(null)
const errorMessage = ref('')
const profileIncomplete = user.profile_complete === false
let refreshTimer

function formatDate(value) {
  return value ? new Date(value).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }) : 'Schedule pending'
}

function trackerStep(status) {
  return status === 'accepted' ? 2 : 1
}

async function loadDashboard() {
  try {
    const response = await fetch('/api/customer/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load your dashboard')
    dashboard.value = data
  } catch (error) { errorMessage.value = error.message }
}

onMounted(() => {
  loadDashboard()
  refreshTimer = setInterval(loadDashboard, 30000)
})
onUnmounted(() => clearInterval(refreshTimer))
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
      <div v-else-if="!dashboard" class="dashboard-loading">Preparing your home-care desk…</div>
      <RouterLink v-if="profileIncomplete" class="profile-reminder" to="/customer/profile?complete=1">
        <span>ONE-TIME SETUP</span>
        <div><strong>Finish your home profile when you’re ready.</strong><small>Add a phone number and address now for a faster booking later.</small></div>
        <b>Complete profile →</b>
      </RouterLink>
      <section v-if="dashboard?.active_booking" class="active-booking-tracker">
        <header><div><p class="workbench-label">ACTIVE BOOKING · #{{ String(dashboard.active_booking.id).padStart(4, '0') }}</p><h2>{{ dashboard.active_booking.service }}</h2></div><RouterLink to="/customer/bookings">View booking →</RouterLink></header>
        <div class="active-booking-summary">
          <div><small>CURRENT UPDATE</small><strong>{{ dashboard.active_booking.status === 'accepted' ? 'Your professional is assigned' : 'Finding the right professional' }}</strong><p>{{ dashboard.active_booking.status === 'accepted' ? `Scheduled for ${formatDate(dashboard.active_booking.scheduled_for)}` : 'HomeServe professionals in your area can now accept this request.' }}</p></div>
          <div v-if="dashboard.active_booking.professional" class="tracker-professional"><span><img v-if="dashboard.active_booking.professional.profile_image_url" :src="dashboard.active_booking.professional.profile_image_url" :alt="dashboard.active_booking.professional.name" /><template v-else>{{ dashboard.active_booking.professional.name.charAt(0).toUpperCase() }}</template></span><div><small>ASSIGNED PROFESSIONAL</small><strong>{{ dashboard.active_booking.professional.name }}</strong></div></div>
        </div>
        <ol class="delivery-progress" :style="{ '--tracker-progress': `${trackerStep(dashboard.active_booking.status) / 3 * 75}%` }">
          <li v-for="(step, index) in ['Booking confirmed', 'Finding professional', 'Professional assigned', 'Service completed']" :key="step" :class="{ 'is-done': index < trackerStep(dashboard.active_booking.status), 'is-current': index === trackerStep(dashboard.active_booking.status) }"><i>{{ index < trackerStep(dashboard.active_booking.status) ? '✓' : index + 1 }}</i><span>{{ step }}</span></li>
        </ol>
        <p class="tracker-refresh-note">Status refreshes automatically every 30 seconds.</p>
      </section>
      <section class="role-page-links customer-page-links">
        <RouterLink to="/customer/services"><span>01</span><div><strong>Explore services</strong><small>Find the right help for your home</small></div><b>→</b></RouterLink>
        <RouterLink to="/customer/bookings"><span>02</span><div><strong>My bookings</strong><small>Track current and previous requests</small></div><b>→</b></RouterLink>
      </section>
    </main>
  </div>
</template>
