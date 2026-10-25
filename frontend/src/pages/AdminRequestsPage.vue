<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import ListPagination from '../components/ListPagination.vue'
import { usePagination } from '../utils/pagination'
import { statusLabel } from '../utils/status'

const requests = ref([])
const filter = ref('all')
const searchQuery = ref('')
const errorMessage = ref('')
const visibleRequests = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return requests.value.filter(item => {
    const matchesFilter = filter.value === 'all' || item.status === filter.value
    const matchesSearch = [item.id, item.service, item.customer, item.professional, item.address].some(value => String(value || '').toLowerCase().includes(query))
    return matchesFilter && matchesSearch
  })
})
const { currentPage, pageCount, paginatedItems: paginatedRequests, resetPage } = usePagination(visibleRequests, 10)
watch([filter, searchQuery], resetPage)

function formatDate(value) {
  if (!value) return 'Not scheduled'
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadRequests() {
  try {
    const response = await fetch('/api/admin/requests', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load requests')
    requests.value = data.requests
  } catch (error) { errorMessage.value = error.message }
}

onMounted(loadRequests)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="requests" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading"><div><p class="workbench-label">OPERATIONS / REQUESTS</p><h1>Follow every job<br />from request to finish.</h1></div><p>Track customer bookings, assigned professionals and current status.</p></header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <div class="list-toolbar"><div class="admin-filters"><button v-for="option in ['all', 'pending', 'accepted', 'completed', 'cancelled']" :key="option" :class="{ active: filter === option }" @click="filter = option">{{ option === 'all' ? 'All' : statusLabel(option) }}</button></div><label class="list-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search ID, service or person" aria-label="Search requests" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label></div>
      <section class="request-records">
        <article v-for="request in paginatedRequests" :key="request.id">
          <code>#{{ String(request.id).padStart(4, '0') }}</code>
          <div><small>Service</small><strong>{{ request.service }}</strong></div>
          <div><small>Customer</small><strong>{{ request.customer }}</strong></div>
          <div><small>Professional</small><strong>{{ request.professional || 'Not assigned' }}</strong></div>
          <div><small>Schedule</small><strong>{{ formatDate(request.scheduled_for) }}</strong></div>
          <span class="record-status" :class="`status-${request.status}`">{{ statusLabel(request.status) }}</span>
        </article>
        <p v-if="!visibleRequests.length && !errorMessage" class="records-empty">No service requests match this filter.</p>
      </section>
      <ListPagination v-model:page="currentPage" :page-count="pageCount" :total="visibleRequests.length" :visible-count="paginatedRequests.length" label="requests" />
    </main>
  </div>
</template>
