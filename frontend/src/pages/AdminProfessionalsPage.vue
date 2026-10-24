<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'

const professionals = ref([])
const errorMessage = ref('')
const successMessage = ref('')
const filter = ref('all')
const searchQuery = ref('')
const visibleProfessionals = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return professionals.value.filter((item) => {
    const matchesFilter = filter.value === 'all' || item.approval_status === filter.value
    const matchesSearch = [item.username, item.email, item.service, item.city].some(value => String(value || '').toLowerCase().includes(query))
    return matchesFilter && matchesSearch
  })
})

async function loadProfessionals() {
  try {
    const response = await fetch('/api/admin/professionals', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load professionals')
    professionals.value = data.professionals
  } catch (error) { errorMessage.value = error.message }
}

async function updateApplication(professional, status) {
  errorMessage.value = ''
  successMessage.value = ''
  let reason = ''
  if (status === 'blocked') {
    reason = window.prompt('Why is this professional being blocked?') || ''
    if (!reason.trim()) return
  }
  try {
    const response = await fetch(`/api/admin/professionals/${professional.id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ status, reason }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update this professional')
    successMessage.value = professional.approval_status === 'blocked' && status === 'approved'
      ? `${professional.username} was unblocked successfully`
      : data.message
    await loadProfessionals()
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(loadProfessionals)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="professionals" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading"><div><p class="workbench-label">PEOPLE / PROFESSIONALS</p><h1>Review the people<br />behind the work.</h1></div><p>Approve applications and monitor professional account status.</p></header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
      <div class="list-toolbar"><div class="admin-filters"><button v-for="option in ['all', 'pending', 'approved', 'blocked']" :key="option" :class="{ active: filter === option }" @click="filter = option">{{ option }}</button></div><label class="list-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search name, service or city" aria-label="Search professionals" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label></div>
      <section class="admin-records professional-records">
        <article v-for="professional in visibleProfessionals" :key="professional.id">
          <span class="list-monogram">{{ professional.username.charAt(0).toUpperCase() }}</span>
          <div class="record-identity"><strong>{{ professional.username }}</strong><small>{{ professional.email }}</small></div>
          <div><small>Service</small><strong>{{ professional.service }}</strong></div>
          <div><small>Location</small><strong>{{ professional.city }}</strong></div>
          <div class="record-rating"><small>Rating</small><strong>{{ professional.average_rating ? `${professional.average_rating} ★` : 'New' }}</strong><small>{{ professional.review_count }} review{{ professional.review_count === 1 ? '' : 's' }}</small></div>
          <span class="record-status" :class="`status-${professional.approval_status}`">{{ professional.approval_status }}</span>
          <div class="approval-actions">
            <button v-if="professional.approval_status === 'pending'" class="approve-action" @click="updateApplication(professional, 'approved')">Approve</button>
            <button v-if="professional.approval_status === 'blocked'" class="unblock-action" @click="updateApplication(professional, 'approved')">Unblock</button>
            <button v-if="professional.approval_status !== 'blocked'" class="block-action" @click="updateApplication(professional, 'blocked')">Block</button>
          </div>
        </article>
        <p v-if="!visibleProfessionals.length" class="records-empty">No professionals match this filter.</p>
      </section>
    </main>
  </div>
</template>
