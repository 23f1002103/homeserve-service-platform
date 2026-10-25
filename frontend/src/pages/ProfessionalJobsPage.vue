<script setup>
import { computed, onMounted, ref } from 'vue'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'

const jobs = ref([])
const availableJobs = ref([])
const activeSection = ref('available')
const filter = ref('all')
const errorMessage = ref('')
const successMessage = ref('')
const acceptingJobId = ref(null)
const completingJobId = ref(null)
const canAcceptJobs = ref(false)
const hasActiveJob = ref(false)
const searchQuery = ref('')
const matchesSearch = (job) => [job.id, job.service, job.customer, job.customer_phone, job.address, job.description, job.area, job.status].some(value => String(value || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()))
const visibleJobs = computed(() => jobs.value.filter(job => (filter.value === 'all' || job.status === filter.value) && matchesSearch(job)))
const visibleAvailableJobs = computed(() => availableJobs.value.filter(matchesSearch))
function formatDate(value) { return value ? new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Not scheduled' }

async function loadJobs() {
  try {
    const response = await fetch('/api/professional/jobs', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load jobs')
    jobs.value = data.jobs
    availableJobs.value = data.available_jobs
    canAcceptJobs.value = data.can_accept_jobs
    hasActiveJob.value = data.has_active_job
  } catch (error) { errorMessage.value = error.message }
}

async function acceptJob(job) {
  errorMessage.value = ''
  successMessage.value = ''
  acceptingJobId.value = job.id
  try {
    const response = await fetch(`/api/professional/jobs/${job.id}/accept`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not accept this job')
    successMessage.value = data.message
    await loadJobs()
    activeSection.value = 'assigned'
    filter.value = 'accepted'
  } catch (error) { errorMessage.value = error.message }
  finally { acceptingJobId.value = null }
}

async function completeJob(job) {
  errorMessage.value = ''
  successMessage.value = ''
  completingJobId.value = job.id
  try {
    const response = await fetch(`/api/professional/jobs/${job.id}/complete`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not complete this job')
    successMessage.value = data.message
    await loadJobs()
  } catch (error) { errorMessage.value = error.message }
  finally { completingJobId.value = null }
}
onMounted(loadJobs)
</script>

<template>
  <div class="workbench professional-workbench"><ProfessionalHeader current="jobs" /><main class="workbench-content role-section-page">
    <header class="role-section-heading"><div><p class="workbench-label">JOB BOARD</p><h1>Available work<br />and your jobs.</h1></div><p>New requests appear only when their service and location match your professional profile.</p></header>
    <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>

    <nav class="job-board-tabs" aria-label="Job sections"><button :class="{ active: activeSection === 'available' }" @click="activeSection = 'available'">Available jobs <span>{{ availableJobs.length }}</span></button><button :class="{ active: activeSection === 'assigned' }" @click="activeSection = 'assigned'">My jobs <span>{{ jobs.length }}</span></button></nav>
    <label class="list-search standalone-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search jobs, customers or locations" aria-label="Search jobs" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label>

    <section v-if="activeSection === 'available'" class="available-job-list">
      <p v-if="!canAcceptJobs" class="job-board-notice">Your account must be approved by the admin before you can accept customer work.</p>
      <p v-if="hasActiveJob" class="job-board-notice">Complete your accepted job before taking another booking.</p>
      <article v-for="job in visibleAvailableJobs" :key="job.id"><header><code>#{{ String(job.id).padStart(4, '0') }}</code><span>{{ job.area }}</span></header><div><p class="workbench-label">{{ job.service }}</p><h2>{{ job.description }}</h2></div><footer><time>{{ formatDate(job.scheduled_for) }}</time><strong>{{ job.price ? `₹${job.price}` : 'Price unavailable' }}</strong><button type="button" :disabled="acceptingJobId === job.id" @click="acceptJob(job)">{{ acceptingJobId === job.id ? 'Accepting…' : 'Accept job' }}</button></footer></article>
      <div v-if="!visibleAvailableJobs.length && canAcceptJobs && !errorMessage" class="empty-job-sheet"><span></span><div><h3>{{ searchQuery ? 'No jobs match your search.' : hasActiveJob ? 'Finish your current job first.' : 'No matching requests right now.' }}</h3><p>{{ hasActiveJob ? 'New matching work will appear again after the accepted job is completed.' : 'Only paid requests matching your service type and selected areas appear here.' }}</p></div></div>
    </section>

    <section v-else>
      <div class="admin-filters"><button v-for="option in ['all', 'accepted', 'completed']" :key="option" :class="{ active: filter === option }" @click="filter = option">{{ option }}</button></div>
      <div class="job-list role-job-list">
        <article v-for="job in visibleJobs" :key="job.id"><span class="job-number">#{{ String(job.id).padStart(3, '0') }}</span><div><strong>{{ job.service }}</strong><small>{{ job.customer }} · {{ job.address }}</small><a v-if="job.customer_phone" class="job-customer-phone" :href="`tel:${job.customer_phone}`">Call {{ job.customer_phone }}</a></div><time>{{ formatDate(job.scheduled_for) }}</time><span class="job-status">{{ job.status }}</span><div class="job-row-actions"><a v-if="job.directions_url" class="job-direction-link" :href="job.directions_url" target="_blank" rel="noopener noreferrer" aria-label="Open customer location in Google Maps"><span class="job-direction-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg></span><span><strong>Directions</strong><small>Google Maps</small></span><b aria-hidden="true">↗</b></a><button v-if="job.status === 'accepted'" class="job-complete-button" type="button" :disabled="completingJobId === job.id" @click="completeJob(job)">{{ completingJobId === job.id ? 'Saving…' : 'Mark completed' }}</button></div></article>
        <div v-if="!visibleJobs.length && !errorMessage" class="empty-job-sheet"><span></span><div><h3>No assigned jobs here.</h3><p>Accept a matching request from the available-jobs tab.</p></div></div>
      </div>
    </section>
  </main></div>
</template>
