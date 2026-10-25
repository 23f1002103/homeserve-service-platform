<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ActionNoticeModal from './ActionNoticeModal.vue'
import CompletionRatingModal from './CompletionRatingModal.vue'

defineProps({ current: { type: String, required: true } })
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const menuOpen = ref(false)
const notification = ref(null)
const reviewPrompt = ref(null)
const reviewPromptError = ref('')
const submittingPromptRating = ref(false)
let notificationTimer
const links = [
  { name: 'Home', path: '/customer/dashboard', key: 'overview' },
  { name: 'Services', path: '/customer/services', key: 'services' },
  { name: 'My bookings', path: '/customer/bookings', key: 'bookings' },
]

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  router.push('/login')
}

async function loadNotification() {
  try {
    const response = await fetch('/api/customer/notifications/unread', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    if (!response.ok) return
    const data = await response.json()
    notification.value = data.notification
  } catch {
    // Navigation should keep working if a background notification check fails.
  }
}

async function loadReviewPrompt() {
  try {
    const response = await fetch('/api/customer/review-prompt', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    if (!response.ok) return
    const data = await response.json()
    reviewPrompt.value = data.review_prompt
  } catch {
    // A review invitation must never block customer navigation.
  }
}

async function submitPromptRating(rating) {
  if (!reviewPrompt.value) return
  reviewPromptError.value = ''
  submittingPromptRating.value = true
  try {
    const response = await fetch(`/api/customer/bookings/${reviewPrompt.value.booking_id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ rating, comment: '' }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not submit your rating')
    reviewPrompt.value = null
  } catch (error) {
    reviewPromptError.value = error.message
  } finally {
    submittingPromptRating.value = false
  }
}

function skipReviewPrompt() {
  reviewPrompt.value = null
  reviewPromptError.value = ''
}

async function closeNotification(openBookings = false) {
  const currentNotification = notification.value
  notification.value = null
  try {
    if (currentNotification) {
      await fetch(`/api/customer/notifications/${currentNotification.id}/read`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      })
    }
  } finally {
    if (openBookings) await router.push('/customer/bookings')
  }
}

onMounted(() => {
  loadReviewPrompt()
  loadNotification()
  notificationTimer = window.setInterval(loadNotification, 45000)
})
onUnmounted(() => window.clearInterval(notificationTimer))
</script>

<template>
  <header class="workbench-bar customer-bar">
    <RouterLink class="workbench-logo" to="/customer/dashboard"><span>HS</span><div><strong>HomeServe</strong><small>Care for your home</small></div></RouterLink>
    <nav class="workbench-tabs" aria-label="Customer navigation">
      <RouterLink v-for="link in links" :key="link.key" :to="link.path" :class="{ 'is-current': current === link.key }">{{ link.name }}</RouterLink>
    </nav>
    <div class="profile-menu">
      <button
        class="profile-menu__trigger"
        type="button"
        :aria-expanded="menuOpen"
        aria-label="Open profile menu"
        @click="menuOpen = !menuOpen"
      >
        <span>{{ (user.username || 'C').charAt(0).toUpperCase() }}</span>
        <div><strong>{{ user.username || 'Customer' }}</strong><small>Customer</small></div>
        <b>⌄</b>
      </button>

      <div v-if="menuOpen" class="profile-menu__panel">
        <p><strong>{{ user.username }}</strong><small>{{ user.email }}</small></p>
        <RouterLink to="/customer/profile" @click="menuOpen = false">My profile</RouterLink>
        <RouterLink to="/" @click="menuOpen = false">HomeServe website</RouterLink>
        <button type="button" @click="logout">Log out</button>
      </div>
    </div>
  </header>
  <ActionNoticeModal
    :open="Boolean(notification) && !reviewPrompt"
    eyebrow="Booking update"
    title="A professional accepted your request."
    :description="notification?.message || 'Open your booking to see who is assigned and what happens next.'"
    primary-label="View booking"
    secondary-label="Got it"
    symbol="✓"
    @primary="closeNotification(true)"
    @secondary="closeNotification(false)"
  />
  <CompletionRatingModal
    :open="Boolean(reviewPrompt)"
    :booking="reviewPrompt"
    :busy="submittingPromptRating"
    :error="reviewPromptError"
    @submit="submitPromptRating"
    @skip="skipReviewPrompt"
  />
</template>
