<script setup>
import { onMounted, ref } from 'vue'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'

const earnings = ref(null)
const selectedWeek = ref('')
const loading = ref(false)
const errorMessage = ref('')

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(value || 0))
}

function formatDate(value) {
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadEarnings() {
  loading.value = true
  errorMessage.value = ''
  try {
    const query = selectedWeek.value ? `?week=${encodeURIComponent(selectedWeek.value)}` : ''
    const response = await fetch(`/api/professional/earnings${query}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load earnings')
    earnings.value = data
    selectedWeek.value = data.week.value
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

onMounted(loadEarnings)
</script>

<template>
  <div class="workbench professional-workbench">
    <ProfessionalHeader current="earnings" />
    <main class="workbench-content role-section-page earnings-page">
      <header class="role-section-heading"><div><p class="workbench-label">EARNINGS LEDGER</p><h1>One week<br />at a time.</h1></div><p>Select any week to see only its completed services and your payout share.</p></header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>

      <section class="earnings-week-control">
        <label>Choose week<input v-model="selectedWeek" type="week" @change="loadEarnings" /></label>
        <p>Only completed, successfully paid jobs count as earnings.</p>
      </section>

      <div v-if="loading && !earnings" class="dashboard-loading">Preparing your weekly ledger…</div>
      <template v-else-if="earnings">
        <section class="earnings-summary">
          <div><small>SELECTED RANGE</small><strong>{{ formatDate(earnings.week.start) }} — {{ formatDate(earnings.week.end) }}</strong></div>
          <div><small>COMPLETED JOBS</small><strong>{{ earnings.completed_jobs.length }}</strong></div>
          <div class="earnings-total"><small>YOUR EARNINGS</small><strong>{{ money(earnings.total_earning) }}</strong></div>
        </section>

        <section class="earnings-ledger">
          <article v-for="job in earnings.completed_jobs" :key="job.id">
            <code>#{{ String(job.id).padStart(4, '0') }}</code>
            <div><strong>{{ job.service }}</strong><small>{{ job.customer }} · completed {{ formatDate(job.completed_at) }}</small></div>
            <div><small>Customer paid</small><strong>{{ money(job.gross_amount) }}</strong></div>
            <div><small>Platform fee ({{ Number(job.commission_rate) }}%)</small><strong>− {{ money(job.platform_fee) }}</strong></div>
            <div class="ledger-earning"><small>Your share</small><strong>{{ money(job.earning) }}</strong></div>
          </article>
          <div v-if="!earnings.completed_jobs.length" class="booking-empty-state"><strong>No completed jobs this week.</strong><p>Choose another week or complete an accepted booking.</p></div>
        </section>
      </template>
    </main>
  </div>
</template>
