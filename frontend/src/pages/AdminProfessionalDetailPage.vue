<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AdminHeader from '../components/AdminHeader.vue'
import ConfirmActionModal from '../components/ConfirmActionModal.vue'
import { statusLabel } from '../utils/status'

const route = useRoute()
const details = ref(null)
const errorMessage = ref('')
const successMessage = ref('')
const pendingAction = ref(null)
const updating = ref(false)

const actionCopy = computed(() => {
  const professional = details.value?.professional
  if (!professional || !pendingAction.value) return {}
  if (pendingAction.value === 'approve') {
    return {
      eyebrow: 'Application decision',
      title: `Approve ${professional.username}?`,
      description: 'The professional will be allowed to verify their location and accept available jobs.',
      confirmLabel: 'Approve professional',
      status: 'approved',
    }
  }
  if (pendingAction.value === 'reactivate') {
    return {
      eyebrow: 'Account control',
      title: `Reactivate ${professional.username}?`,
      description: 'The professional will regain access to available jobs after completing location verification.',
      confirmLabel: 'Reactivate account',
      status: 'approved',
    }
  }
  const rejecting = professional.approval_status === 'pending'
  return {
    eyebrow: rejecting ? 'Application decision' : 'Account control',
    title: rejecting ? `Reject ${professional.username}?` : `Suspend ${professional.username}?`,
    description: rejecting
      ? 'The application will be rejected and the reason will remain visible in this admin record.'
      : 'The professional cannot be suspended while handling an active job. The reason will remain visible in this admin record.',
    confirmLabel: rejecting ? 'Reject application' : 'Suspend account',
    status: 'blocked',
    reasonLabel: rejecting ? 'Reason for rejection' : 'Reason for suspension',
  }
})

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(value || 0))
}

function formatDate(value) {
  if (!value) return 'Not available'
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function professionalStatusLabel(status) {
  return { pending: 'Pending review', approved: 'Approved', blocked: 'Restricted' }[status] || status
}

async function loadProfessional() {
  errorMessage.value = ''
  try {
    const response = await fetch(`/api/admin/professionals/${route.params.id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load this professional')
    details.value = data
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function updateStatus(reason = '') {
  if (!details.value || !actionCopy.value.status) return
  updating.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await fetch(`/api/admin/professionals/${details.value.professional.id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ status: actionCopy.value.status, reason }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update this professional')
    successMessage.value = actionCopy.value.status === 'approved' ? 'Professional account approved and active.' : 'Professional account updated.'
    pendingAction.value = null
    await loadProfessional()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    updating.value = false
  }
}

onMounted(loadProfessional)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="professionals" />
    <main class="workbench-content admin-person-detail">
      <RouterLink class="admin-back-link" to="/admin/professionals">← Back to professionals</RouterLink>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
      <div v-if="!details && !errorMessage" class="dashboard-loading">Loading professional record…</div>

      <template v-if="details">
        <header class="person-detail-heading">
          <div>
            <p class="workbench-label">PROFESSIONAL RECORD / #{{ String(details.professional.id).padStart(4, '0') }}</p>
            <h1>{{ details.professional.username }}</h1>
          </div>
          <div class="person-heading-actions">
            <span class="record-status" :class="`status-${details.professional.approval_status}`">{{ professionalStatusLabel(details.professional.approval_status) }}</span>
            <button v-if="details.professional.approval_status === 'pending'" class="person-action-primary" @click="pendingAction = 'approve'">Approve</button>
            <button v-if="details.professional.approval_status === 'blocked'" class="person-action-primary" @click="pendingAction = 'reactivate'">Reactivate</button>
            <button v-if="details.professional.approval_status !== 'blocked'" class="person-action-danger" @click="pendingAction = 'restrict'">{{ details.professional.approval_status === 'pending' ? 'Reject' : 'Suspend' }}</button>
          </div>
        </header>

        <section class="person-summary-grid">
          <article><small>TOTAL JOBS</small><strong>{{ details.summary.total_jobs }}</strong></article>
          <article><small>ACTIVE JOBS</small><strong>{{ details.summary.active_jobs }}</strong></article>
          <article><small>COMPLETED</small><strong>{{ details.summary.completed_jobs }}</strong></article>
          <article><small>TOTAL EARNINGS</small><strong>{{ money(details.summary.total_earnings) }}</strong></article>
        </section>

        <section class="person-profile-sheet">
          <div class="person-profile-intro">
            <span>{{ details.professional.username.charAt(0).toUpperCase() }}</span>
            <div><p class="workbench-label">PROFILE & VERIFICATION</p><h2>{{ details.professional.service }} professional</h2><small>{{ details.professional.average_rating ? `${details.professional.average_rating} ★ from ${details.professional.review_count} review(s)` : 'No customer ratings yet' }}</small></div>
          </div>
          <dl>
            <div><dt>Email</dt><dd>{{ details.professional.email }}</dd></div>
            <div><dt>Phone</dt><dd>{{ details.professional.phone_number || 'Not provided' }}</dd></div>
            <div><dt>Experience</dt><dd>{{ details.professional.experience_years ?? 0 }} year(s)</dd></div>
            <div><dt>Address</dt><dd>{{ details.professional.address }}, {{ details.professional.city }}, {{ details.professional.state }} — {{ details.professional.pin_code }}</dd></div>
            <div><dt>Current service area</dt><dd>{{ details.professional.active_service_area ? `${details.professional.active_service_area.city}, ${details.professional.active_service_area.state}` : 'Not connected' }}</dd></div>
            <div><dt>Last GPS verification</dt><dd>{{ formatDate(details.professional.location_verified_at) }}</dd></div>
            <div v-if="details.professional.block_reason" class="person-restriction-reason"><dt>Admin reason</dt><dd>{{ details.professional.block_reason }}</dd></div>
          </dl>
        </section>

        <section class="person-history-section">
          <header><div><p class="workbench-label">JOB HISTORY</p><h2>Assigned service work.</h2></div><span>{{ details.jobs.length }} record{{ details.jobs.length === 1 ? '' : 's' }}</span></header>
          <div class="person-history-list">
            <article v-for="job in details.jobs" :key="job.id">
              <code>#{{ String(job.id).padStart(4, '0') }}</code>
              <div><small>Service</small><strong>{{ job.service }}</strong></div>
              <div><small>Customer</small><strong>{{ job.customer }}</strong></div>
              <div><small>Scheduled</small><strong>{{ formatDate(job.scheduled_for) }}</strong></div>
              <div><small>Earning</small><strong>{{ job.payment?.status === 'completed' ? money(job.payment.professional_earning) : 'Not earned' }}</strong></div>
              <span class="record-status" :class="`status-${job.status}`">{{ statusLabel(job.status) }}</span>
            </article>
            <p v-if="!details.jobs.length" class="records-empty">No jobs have been assigned to this professional yet.</p>
          </div>
        </section>
      </template>
    </main>

    <ConfirmActionModal
      :open="Boolean(pendingAction)"
      :eyebrow="actionCopy.eyebrow"
      :title="actionCopy.title || 'Update professional?'"
      :description="actionCopy.description || ''"
      :confirm-label="actionCopy.confirmLabel"
      :reason-label="actionCopy.reasonLabel"
      reason-placeholder="Add a clear reason for this decision"
      :busy="updating"
      :danger="actionCopy.status === 'blocked'"
      @confirm="updateStatus"
      @cancel="pendingAction = null"
    />
  </div>
</template>
