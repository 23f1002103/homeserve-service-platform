<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CustomerHeader from '../components/CustomerHeader.vue'
import { statusLabel } from '../utils/status'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const dashboard = ref(null)
const errorMessage = ref('')
const activeBookingIndex = ref(0)
const profileIncomplete = user.profile_complete === false
const swipeStartX = ref(null)
let refreshTimer

const activeBookings = computed(() => dashboard.value?.active_bookings || (dashboard.value?.active_booking ? [dashboard.value.active_booking] : []))
const activeBooking = computed(() => activeBookings.value[activeBookingIndex.value] || null)
const activePackageOrders = computed(() => dashboard.value?.active_package_orders || [])

function formatDate(value) {
  return value ? new Date(value).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }) : 'Schedule pending'
}

function trackerStep(status) {
  return status === 'accepted' ? 2 : 1
}

async function loadDashboard() {
  try {
    const selectedBookingId = activeBooking.value?.id
    const response = await fetch('/api/customer/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load your dashboard')
    dashboard.value = data
    const refreshedIndex = data.active_bookings?.findIndex((booking) => booking.id === selectedBookingId) ?? -1
    activeBookingIndex.value = refreshedIndex >= 0 ? refreshedIndex : 0
  } catch (error) { errorMessage.value = error.message }
}

function showBooking(offset) {
  if (activeBookings.value.length < 2) return
  activeBookingIndex.value = (activeBookingIndex.value + offset + activeBookings.value.length) % activeBookings.value.length
}

function beginBookingSwipe(event) {
  swipeStartX.value = event.touches[0]?.clientX ?? null
}

function finishBookingSwipe(event) {
  if (swipeStartX.value === null) return
  const distance = (event.changedTouches[0]?.clientX ?? swipeStartX.value) - swipeStartX.value
  swipeStartX.value = null
  if (Math.abs(distance) < 45) return
  showBooking(distance < 0 ? 1 : -1)
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
    <main class="workbench-content customer-content customer-app-home">
      <section class="customer-app-welcome">
        <div><span>HomeServe customer</span><h1>Hello, {{ user.username || 'Customer' }}</h1><p>Book trusted help and follow every visit from one place.</p></div>
        <RouterLink to="/customer/services"><span>＋</span> Book a service</RouterLink>
      </section>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <div v-else-if="!dashboard" class="dashboard-loading">Loading your dashboard…</div>
      <section v-if="dashboard" class="customer-app-summary">
        <div><strong>{{ dashboard.open_bookings }}</strong><span>Open orders</span></div>
        <i></i>
        <div><strong>{{ dashboard.completed_bookings }}</strong><span>Completed</span></div>
        <i></i>
        <div class="summary-location"><strong>{{ dashboard.city || 'Not added' }}</strong><span>Service city</span></div>
      </section>
      <RouterLink v-if="profileIncomplete" class="profile-reminder" to="/customer/profile?complete=1">
        <span>PROFILE</span>
        <div><strong>Complete your contact and address details</strong><small>Required before your first booking.</small></div>
        <b>Complete profile →</b>
      </RouterLink>
      <section v-if="activePackageOrders.length" class="dashboard-package-orders">
        <header><div><span>COMBO ORDERS</span><h2>Services working together</h2></div><RouterLink to="/customer/bookings">View all orders →</RouterLink></header>
        <article v-for="order in activePackageOrders" :key="order.id">
          <div class="dashboard-package-title"><span>PKG-{{ String(order.id).padStart(4, '0') }}</span><h3>{{ order.name }}</h3><small>{{ statusLabel(order.status) }}</small></div>
          <ol><li v-for="service in order.services" :key="service.name"><i :class="`is-${service.status}`">{{ service.status === 'completed' ? '✓' : service.status === 'accepted' ? '●' : '○' }}</i><div><strong>{{ service.name }}</strong><small>{{ service.professional || statusLabel(service.status) }}</small></div></li></ol>
        </article>
      </section>
      <section v-if="activeBooking" class="active-booking-tracker" @touchstart.passive="beginBookingSwipe" @touchend.passive="finishBookingSwipe">
        <header><div><p class="workbench-label">ACTIVE BOOKING · #{{ String(activeBooking.id).padStart(4, '0') }}</p><h2>{{ activeBooking.service }}</h2></div><div class="tracker-header-actions"><div v-if="activeBookings.length > 1" class="tracker-pagination" aria-label="Choose active booking"><button type="button" aria-label="Previous active booking" @click="showBooking(-1)">←</button><span>{{ activeBookingIndex + 1 }} / {{ activeBookings.length }}</span><button type="button" aria-label="Next active booking" @click="showBooking(1)">→</button></div><RouterLink to="/customer/bookings">Open details</RouterLink></div></header>
        <div class="active-booking-summary">
          <div><small>CURRENT UPDATE</small><strong>{{ activeBooking.status === 'accepted' ? 'Your professional is assigned' : 'Finding the right professional' }}</strong><p>{{ activeBooking.status === 'accepted' ? `Scheduled for ${formatDate(activeBooking.scheduled_for)}` : 'HomeServe professionals in your area can now accept this request.' }}</p></div>
          <div v-if="activeBooking.professional" class="tracker-professional"><span><img v-if="activeBooking.professional.profile_image_url" :src="activeBooking.professional.profile_image_url" :alt="activeBooking.professional.name" /><template v-else>{{ activeBooking.professional.name.charAt(0).toUpperCase() }}</template></span><div><small>ASSIGNED PROFESSIONAL</small><strong>{{ activeBooking.professional.name }}</strong></div></div>
        </div>
        <ol class="delivery-progress" :style="{ '--tracker-progress': `${trackerStep(activeBooking.status) / 3 * 75}%` }">
          <li v-for="(step, index) in ['Booking confirmed', 'Finding professional', 'Professional assigned', 'Service completed']" :key="step" :class="{ 'is-done': index < trackerStep(activeBooking.status), 'is-current': index === trackerStep(activeBooking.status) }"><i>{{ index < trackerStep(activeBooking.status) ? '✓' : index + 1 }}</i><span>{{ step }}</span></li>
        </ol>
        <p class="tracker-refresh-note">{{ activeBookings.length > 1 ? 'Swipe or use the arrows to see every active booking. ' : '' }}Status refreshes automatically every 30 seconds.</p>
      </section>
      <section class="customer-quick-actions">
        <RouterLink to="/customer/services"><span>⌕</span><div><strong>Browse services</strong><small>Services and combo packages</small></div><b>→</b></RouterLink>
        <RouterLink to="/customer/bookings"><span>▤</span><div><strong>Orders</strong><small>Track visits, payments and reviews</small></div><b>→</b></RouterLink>
        <RouterLink to="/customer/profile"><span>♙</span><div><strong>Profile</strong><small>Contact and service address</small></div><b>→</b></RouterLink>
      </section>
    </main>
  </div>
</template>
