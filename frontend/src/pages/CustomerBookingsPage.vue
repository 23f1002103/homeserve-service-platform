<script setup>
import { computed, onMounted, ref } from 'vue'
import CustomerHeader from '../components/CustomerHeader.vue'
const bookings = ref([])
const filter = ref('all')
const searchQuery = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const expandedBookingId = ref(null)
const reviewingId = ref(null)
const rating = ref(5)
const reviewComment = ref('')
const submittingReview = ref(false)
const cancellingBookingId = ref(null)
const downloadingInvoiceId = ref(null)
const visibleBookings = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return bookings.value.filter(item => {
    const matchesFilter = filter.value === 'all' || item.status === filter.value
    const matchesSearch = [item.id, item.service, item.professional, item.address, item.status].some(value => String(value || '').toLowerCase().includes(query))
    return matchesFilter && matchesSearch
  })
})
const openBookingCount = computed(() => bookings.value.filter(item => ['pending', 'accepted'].includes(item.status)).length)
function formatDate(value) { return value ? new Date(value).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'Not scheduled' }
function paymentLabel(value) { return value === 'demo_upi' ? 'HomeServe Demo UPI' : 'Payment method unavailable' }
function toggleBooking(bookingId) { expandedBookingId.value = expandedBookingId.value === bookingId ? null : bookingId }
function startReview(booking) { reviewingId.value = booking.id; rating.value = 5; reviewComment.value = ''; expandedBookingId.value = booking.id }
async function loadBookings() {
  try {
    const response = await fetch('/api/customer/bookings', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load bookings')
    bookings.value = data.bookings
  } catch (error) { errorMessage.value = error.message }
}

async function submitReview(booking) {
  errorMessage.value = ''
  successMessage.value = ''
  submittingReview.value = true
  try {
    const response = await fetch(`/api/customer/bookings/${booking.id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ rating: rating.value, comment: reviewComment.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not submit review')
    successMessage.value = data.message
    reviewingId.value = null
    await loadBookings()
  } catch (error) { errorMessage.value = error.message }
  finally { submittingReview.value = false }
}

async function cancelBooking(booking) {
  const warning = booking.payment_status === 'completed'
    ? 'Cancel this booking? Its demo payment will be marked as refunded.'
    : 'Cancel this booking? This cannot be undone.'
  if (!window.confirm(warning)) return

  errorMessage.value = ''
  successMessage.value = ''
  cancellingBookingId.value = booking.id
  try {
    const response = await fetch(`/api/customer/bookings/${booking.id}/cancel`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not cancel this booking')
    successMessage.value = data.payment_status === 'refunded'
      ? 'Booking cancelled and demo payment marked as refunded'
      : data.message
    await loadBookings()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    cancellingBookingId.value = null
  }
}

async function downloadInvoice(booking) {
  errorMessage.value = ''
  downloadingInvoiceId.value = booking.id
  try {
    const response = await fetch(`/api/customer/bookings/${booking.id}/invoice`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.message || 'Could not download invoice')
    }
    const file = await response.blob()
    const url = URL.createObjectURL(file)
    const link = document.createElement('a')
    link.href = url
    link.download = `homeserve-invoice-${booking.id}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    downloadingInvoiceId.value = null
  }
}
onMounted(loadBookings)
</script>

<template>
  <div class="workbench customer-workbench"><CustomerHeader current="bookings" /><main class="workbench-content role-section-page customer-bookings-page">
    <header class="role-section-heading"><div><p class="workbench-label">MY BOOKINGS</p><h1>Your home-care<br />timeline.</h1></div><p>See what happens next, who is assigned and when each professional is expected.</p></header>
    <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
    <section class="booking-overview-strip"><div><small>TOTAL REQUESTS</small><strong>{{ bookings.length }}</strong></div><div><small>OPEN NOW</small><strong>{{ openBookingCount }}</strong></div><RouterLink to="/customer/services">Book another service →</RouterLink></section>
    <div class="list-toolbar booking-filters"><div class="admin-filters"><button v-for="option in ['all', 'payment_pending', 'pending', 'accepted', 'completed', 'cancelled']" :key="option" :class="{ active: filter === option }" @click="filter = option">{{ option.replace('_', ' ') }}</button></div><label class="list-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search bookings" aria-label="Search bookings" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label></div>
    <section class="booking-compact-list">
      <article v-for="booking in visibleBookings" :key="booking.id" :class="{ 'is-open': expandedBookingId === booking.id }">
        <button class="booking-compact-summary" type="button" @click="toggleBooking(booking.id)">
          <span class="booking-compact-id"><code>#{{ String(booking.id).padStart(4, '0') }}</code><strong>{{ booking.service }}</strong></span>
          <span><small>SCHEDULE</small><strong>{{ formatDate(booking.scheduled_for) }}</strong></span>
          <span><small>PROFESSIONAL</small><strong>{{ booking.professional || 'Waiting for match' }}</strong></span>
          <span><small>AMOUNT</small><strong>{{ booking.price ? `₹${booking.price}` : '—' }}</strong></span>
          <span class="record-status" :class="`status-${booking.status}`">{{ booking.status.replace('_', ' ') }}</span>
          <b>{{ expandedBookingId === booking.id ? '−' : '+' }}</b>
        </button>

        <div v-if="expandedBookingId === booking.id" class="booking-compact-details">
          <div class="booking-detail-copy"><div><small>PROBLEM DETAILS</small><p>{{ booking.description || 'No extra details provided.' }}</p></div><div><small>SERVICE ADDRESS</small><p>{{ booking.address }}</p></div><div><small>PAYMENT</small><p>{{ paymentLabel(booking.payment_method) }} · {{ booking.payment_status || 'pending' }}</p></div></div>
          <div v-if="booking.payment_status === 'completed'" class="booking-document-row"><div><strong>Payment invoice</strong><small>A PDF copy for your records.</small></div><button type="button" :disabled="downloadingInvoiceId === booking.id" @click="downloadInvoice(booking)">{{ downloadingInvoiceId === booking.id ? 'Preparing…' : 'Download PDF' }}</button></div>
          <div v-if="booking.status === 'cancelled'" class="booking-cancelled-note"><span>×</span><div><strong>Booking cancelled</strong><p>No professional can accept this request. {{ booking.payment_status === 'refunded' ? 'The demo payment is marked as refunded.' : '' }}</p></div></div>
          <div v-else class="booking-progress" :class="`booking-progress--${booking.status}`"><span>Requested</span><i></i><span>Accepted</span><i></i><span>Completed</span></div>

          <div v-if="!booking.professional && ['payment_pending', 'pending'].includes(booking.status)" class="booking-cancel-action"><div><strong>Plans changed?</strong><small>You can cancel until a professional accepts this booking.</small></div><button type="button" :disabled="cancellingBookingId === booking.id" @click="cancelBooking(booking)">{{ cancellingBookingId === booking.id ? 'Cancelling…' : 'Cancel booking' }}</button></div>

          <section v-if="booking.status === 'completed'" class="booking-review-panel">
            <div v-if="booking.review" class="submitted-review"><span>{{ '★'.repeat(booking.review.rating) }}{{ '☆'.repeat(5 - booking.review.rating) }}</span><div><strong>Your review</strong><p>{{ booking.review.comment || 'No written comment.' }}</p></div></div>
            <form v-else-if="reviewingId === booking.id" @submit.prevent="submitReview(booking)"><div class="rating-picker"><span>YOUR RATING</span><button v-for="star in 5" :key="star" type="button" :class="{ active: star <= rating }" :aria-label="`${star} stars`" @click="rating = star">★</button></div><textarea v-model.trim="reviewComment" maxlength="500" rows="3" placeholder="How was the service?"></textarea><div><small>{{ reviewComment.length }}/500</small><button type="submit" :disabled="submittingReview">{{ submittingReview ? 'Submitting…' : 'Submit review' }}</button></div></form>
            <button v-else class="review-start-button" type="button" @click="startReview(booking)">Rate this service</button>
          </section>
        </div>
      </article>
      <div v-if="!visibleBookings.length && !errorMessage" class="booking-empty-state"><strong>No bookings here yet.</strong><p>Choose a household service whenever your home needs care.</p><RouterLink to="/customer/services">Explore services</RouterLink></div>
    </section>
  </main></div>
</template>
