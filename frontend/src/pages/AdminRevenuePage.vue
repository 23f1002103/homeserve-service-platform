<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import ListPagination from '../components/ListPagination.vue'
import { usePagination } from '../utils/pagination'

const report = ref(null)
const startDate = ref('')
const endDate = ref('')
const loading = ref(false)
const exporting = ref(false)
const errorMessage = ref('')
const transactions = computed(() => report.value?.transactions || [])
const { currentPage, pageCount, paginatedItems: paginatedTransactions, resetPage } = usePagination(transactions, 10)

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(value || 0))
}

function formatDate(value) {
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadRevenue() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (startDate.value) params.set('start_date', startDate.value)
    if (endDate.value) params.set('end_date', endDate.value)
    const query = params.toString() ? `?${params}` : ''
    const response = await fetch(`/api/admin/revenue${query}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load revenue')
    report.value = data
    resetPage()
    startDate.value = data.range.start
    endDate.value = data.range.end
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function downloadRevenueSheet() {
  exporting.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams({ start_date: startDate.value, end_date: endDate.value })
    const response = await fetch(`/api/admin/revenue/export?${params}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.message || 'Could not download revenue sheet')
    }
    const file = await response.blob()
    const url = URL.createObjectURL(file)
    const link = document.createElement('a')
    link.href = url
    link.download = `homeserve-revenue-${startDate.value}-to-${endDate.value}.csv`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    exporting.value = false
  }
}

onMounted(loadRevenue)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="revenue" />
    <main class="workbench-content admin-section-page revenue-page">
      <header class="section-page-heading"><div><p class="workbench-label">FINANCE / REVENUE</p><h1>Follow the value<br />behind every job.</h1></div><p>See all-time platform revenue, then choose a date range for a focused transaction report.</p></header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>

      <form class="revenue-range-control" @submit.prevent="loadRevenue">
        <label>From<input v-model="startDate" type="date" :max="endDate || undefined" required /></label>
        <label>To<input v-model="endDate" type="date" :min="startDate || undefined" required /></label>
        <button type="submit" :disabled="loading">{{ loading ? 'Loading…' : 'Apply range' }}</button>
        <button class="revenue-export-button" type="button" :disabled="exporting || !report" @click="downloadRevenueSheet">{{ exporting ? 'Preparing…' : 'Download CSV' }}</button>
        <p>Revenue is recognized only after a paid service is marked completed.</p>
      </form>

      <div v-if="loading && !report" class="dashboard-loading">Preparing the revenue report…</div>
      <template v-else-if="report">
        <section class="revenue-all-time">
          <div><p class="workbench-label">ALL-TIME PLATFORM REVENUE</p><strong>{{ money(report.all_time.platform_revenue) }}</strong><small>{{ report.all_time.completed_jobs }} completed jobs since launch</small></div>
          <div><small>ALL CUSTOMER PAYMENTS</small><strong>{{ money(report.all_time.gross_payments) }}</strong></div>
          <div><small>ALL PROFESSIONAL PAYOUTS</small><strong>{{ money(report.all_time.professional_payouts) }}</strong></div>
        </section>

        <div class="revenue-range-heading"><div><p class="workbench-label">SELECTED RANGE</p><h2>{{ formatDate(report.range.start) }} — {{ formatDate(report.range.end) }}</h2></div><span>{{ report.selected.completed_jobs }} completed jobs</span></div>
        <section class="revenue-summary-grid">
          <article><small>CUSTOMERS PAID</small><strong>{{ money(report.selected.gross_payments) }}</strong></article>
          <article class="is-revenue"><small>HOMESERVE REVENUE</small><strong>{{ money(report.selected.platform_revenue) }}</strong></article>
          <article><small>PROFESSIONAL PAYOUTS</small><strong>{{ money(report.selected.professional_payouts) }}</strong></article>
        </section>

        <section class="revenue-ledger">
          <article v-for="transaction in paginatedTransactions" :key="transaction.booking_id">
            <code>#{{ String(transaction.booking_id).padStart(4, '0') }}</code>
            <div><strong>{{ transaction.service }}</strong><small>{{ transaction.customer }} → {{ transaction.professional }}</small></div>
            <div><small>Completed</small><strong>{{ formatDate(transaction.completed_at) }}</strong></div>
            <div><small>Customer paid</small><strong>{{ money(transaction.gross_amount) }}</strong></div>
            <div><small>Professional</small><strong>{{ money(transaction.professional_payout) }}</strong></div>
            <div class="revenue-ledger-fee"><small>Revenue · {{ Number(transaction.commission_rate) }}%</small><strong>{{ money(transaction.platform_fee) }}</strong></div>
          </article>
          <div v-if="!report.transactions.length" class="booking-empty-state"><strong>No revenue in this range.</strong><p>Try a wider date range or wait for paid jobs to be completed.</p></div>
        </section>
        <ListPagination v-model:page="currentPage" :page-count="pageCount" :total="transactions.length" :visible-count="paginatedTransactions.length" label="transactions" />
      </template>
    </main>
  </div>
</template>
