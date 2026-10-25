<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import ListPagination from '../components/ListPagination.vue'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'
import { usePagination } from '../utils/pagination'

const areas = ref([])
const selectedAreaIds = ref([])
const errorMessage = ref('')
const successMessage = ref('')
const unavailableLocation = ref(null)
const areaChoices = ref(null)
const detecting = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const stateFilter = ref('all')
const cityFilter = ref('all')
const normalized = (value) => String(value || '').trim().toLowerCase()
const stateOptions = computed(() => [...new Map(
  areas.value.map(area => [normalized(area.state), area.state]),
).entries()].map(([value, label]) => ({ value, label })).sort((first, second) => first.label.localeCompare(second.label)))
const cityOptions = computed(() => {
  if (stateFilter.value === 'all') return []
  return [...new Map(
    areas.value
      .filter(area => normalized(area.state) === stateFilter.value)
      .map(area => [normalized(area.city), area.city]),
  ).entries()].map(([value, label]) => ({ value, label })).sort((first, second) => first.label.localeCompare(second.label))
})
const visibleAreas = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return areas.value
    .filter(area => stateFilter.value === 'all' || normalized(area.state) === stateFilter.value)
    .filter(area => cityFilter.value === 'all' || normalized(area.city) === cityFilter.value)
    .filter(area => [area.city, area.state, area.pin_code].some(value => String(value || '').toLowerCase().includes(query)))
    .sort((first, second) => first.state.localeCompare(second.state) || first.city.localeCompare(second.city) || first.pin_code.localeCompare(second.pin_code))
})
const { currentPage, pageCount, paginatedItems: paginatedAreas, resetPage } = usePagination(visibleAreas, 12)

watch(stateFilter, () => {
  cityFilter.value = 'all'
  resetPage()
})
watch([cityFilter, searchQuery], resetPage)

function authHeaders(includeJson = false) {
  const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  if (includeJson) headers['Content-Type'] = 'application/json'
  return headers
}

async function loadAreas() {
  try {
    const response = await fetch('/api/professional/service-areas', { headers: authHeaders() })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load service areas')
    areas.value = data.available_areas
    selectedAreaIds.value = data.selected_area_ids
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function saveAreas() {
  errorMessage.value = ''
  successMessage.value = ''
  saving.value = true
  try {
    const response = await fetch('/api/professional/service-areas', {
      method: 'PATCH',
      headers: authHeaders(true),
      body: JSON.stringify({ area_ids: selectedAreaIds.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not save service areas')
    successMessage.value = data.message
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    saving.value = false
  }
}

function detectLocation() {
  errorMessage.value = ''
  successMessage.value = ''
  unavailableLocation.value = null
  if (!navigator.geolocation) {
    errorMessage.value = 'Location detection is not supported by this browser'
    return
  }

  detecting.value = true
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const response = await fetch('/api/professional/detect-service-area', {
          method: 'POST',
          headers: authHeaders(true),
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          }),
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.message || 'Could not check your location')

        if (data.matched_area) {
          if (!selectedAreaIds.value.includes(data.matched_area.id)) {
            selectedAreaIds.value.push(data.matched_area.id)
          }
          successMessage.value = `${data.matched_area.city} was detected and selected. Press Save to confirm.`
        } else {
          unavailableLocation.value = data.detected_location
        }
      } catch (error) {
        errorMessage.value = error.message
      } finally {
        detecting.value = false
      }
    },
    () => {
      detecting.value = false
      errorMessage.value = 'Location permission was denied or your location could not be found'
    },
    { enableHighAccuracy: false, timeout: 10000 },
  )
}

function chooseAnotherArea() {
  areaChoices.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(loadAreas)
</script>

<template>
  <div class="workbench professional-workbench">
    <ProfessionalHeader current="areas" />
    <main class="workbench-content role-section-page">
      <header class="role-section-heading">
        <div><p class="workbench-label">SERVICE MAP</p><h1>Where you<br />can work.</h1></div>
        <p>Select every area where you accept customer jobs. Detection is optional and never changes the list without your confirmation.</p>
      </header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>

      <section v-if="unavailableLocation" class="area-unavailable">
        <div>
          <p class="workbench-label">CURRENT LOCATION</p>
          <h2>HomeServe is not available here yet.</h2>
          <p>
            We detected
            <strong>{{ unavailableLocation.city || 'your current area' }}</strong>
            <template v-if="unavailableLocation.pin_code"> — {{ unavailableLocation.pin_code }}</template>.
            It is not in the admin's approved service-area list.
          </p>
        </div>
        <div class="area-unavailable__actions">
          <button type="button" @click="chooseAnotherArea">Choose another area</button>
          <button type="button" :disabled="detecting" @click="detectLocation">Try again</button>
        </div>
      </section>

      <div class="area-actions">
        <button type="button" :disabled="detecting" @click="detectLocation">{{ detecting ? 'Detecting…' : 'Detect my current area' }}</button>
        <button type="button" :disabled="saving" @click="saveAreas">{{ saving ? 'Saving…' : 'Save selected areas' }}</button>
      </div>
      <section class="area-filter-panel" aria-label="Filter service areas">
        <label>State<select v-model="stateFilter"><option value="all">All states</option><option v-for="state in stateOptions" :key="state.value" :value="state.value">{{ state.label }}</option></select></label>
        <label>City<select v-model="cityFilter" :disabled="stateFilter === 'all'"><option value="all">{{ stateFilter === 'all' ? 'Select a state first' : 'All cities' }}</option><option v-for="city in cityOptions" :key="city.value" :value="city.value">{{ city.label }}</option></select></label>
        <label class="list-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search PIN or place" aria-label="Search service areas" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label>
        <span><strong>{{ selectedAreaIds.length }}</strong> selected</span>
      </section>
      <section ref="areaChoices" class="area-choice-grid">
        <label v-for="area in paginatedAreas" :key="area.id" :class="{ 'is-selected': selectedAreaIds.includes(area.id) }">
          <input v-model="selectedAreaIds" type="checkbox" :value="area.id" />
          <span><strong>{{ area.city }}</strong><small>{{ area.state }}</small><code>{{ area.pin_code }}</code></span>
        </label>
        <div v-if="!visibleAreas.length && !errorMessage" class="area-empty">
          <strong>{{ searchQuery ? 'No areas match your search.' : 'No service areas are available.' }}</strong><p v-if="!searchQuery">The admin must create service areas first.</p>
        </div>
      </section>
      <ListPagination v-model:page="currentPage" :page-count="pageCount" :total="visibleAreas.length" :visible-count="paginatedAreas.length" label="service areas" />
    </main>
  </div>
</template>
