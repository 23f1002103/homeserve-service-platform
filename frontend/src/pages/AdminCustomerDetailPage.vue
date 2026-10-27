<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AdminHeader from '../components/AdminHeader.vue'
import { statusLabel } from '../utils/status'

const route = useRoute()
const details = ref(null)
const errorMessage = ref('')

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(value || 0))
}

function formatDate(value) {
  if (!value) return 'Not scheduled'
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadCustomer() {
  errorMessage.value = ''
  try {
    const response = await fetch(`/api/admin/customers/${route.params.id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load this customer')
    details.value = data
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(loadCustomer)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="customers" />
    <main class="workbench-content admin-person-detail">
      <RouterLink class="admin-back-link" to="/admin/customers">← Back to customers</RouterLink>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <div v-if="!details && !errorMessage" class="dashboard-loading">Loading customer record…</div>

      <template v-if="details">
        <header class="person-detail-heading">
          <div>
            <p class="workbench-label">CUSTOMER RECORD / #{{ String(details.customer.id).padStart(4, '0') }}</p>
            <h1>{{ details.customer.username }}</h1>
          </div>
          <p>Read-only account information and the customer's complete HomeServe booking history.</p>
        </header>

        <section class="person-summary-grid">
          <article><small>TOTAL BOOKINGS</small><strong>{{ details.summary.total_bookings }}</strong></article>
          <article><small>ACTIVE BOOKINGS</small><strong>{{ details.summary.active_bookings }}</strong></article>
          <article><small>COMPLETED</small><strong>{{ details.summary.completed_bookings }}</strong></article>
          <article><small>TOTAL PAID</small><strong>{{ money(details.summary.total_spent) }}</strong></article>
        </section>

        <section class="person-profile-sheet">
          <div class="person-profile-intro">
            <span>{{ details.customer.username.charAt(0).toUpperCase() }}</span>
            <div><p class="workbench-label">ACCOUNT DETAILS</p><h2>Customer profile</h2></div>
          </div>
          <dl>
            <div><dt>Email</dt><dd>{{ details.customer.email }}</dd></div>
            <div><dt>Phone</dt><dd>{{ details.customer.phone_number || 'Not provided' }}</dd></div>
            <div><dt>Address</dt><dd>{{ details.customer.address }}</dd></div>
            <div><dt>City / State</dt><dd>{{ details.customer.city }}, {{ details.customer.state }}</dd></div>
            <div><dt>Pin code</dt><dd>{{ details.customer.pin_code }}</dd></div>
          </dl>
        </section>

        <section class="person-history-section">
          <header><div><p class="workbench-label">BOOKING HISTORY</p><h2>Every service request.</h2></div><span>{{ details.bookings.length }} record{{ details.bookings.length === 1 ? '' : 's' }}</span></header>
          <div class="person-history-list">
            <article v-for="booking in details.bookings" :key="booking.id">
              <code>#{{ String(booking.id).padStart(4, '0') }}</code>
              <div><small>Service</small><strong>{{ booking.service }}</strong></div>
              <div><small>Professional</small><strong>{{ booking.professional || 'Not assigned' }}</strong></div>
              <div><small>Scheduled</small><strong>{{ formatDate(booking.scheduled_for) }}</strong></div>
              <div><small>Payment</small><strong>{{ booking.payment ? `${money(booking.payment.amount)} · ${statusLabel(booking.payment.status)}` : 'No payment' }}</strong></div>
              <span class="record-status" :class="`status-${booking.status}`">{{ statusLabel(booking.status) }}</span>
            </article>
            <p v-if="!details.bookings.length" class="records-empty">This customer has not made a booking yet.</p>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>
