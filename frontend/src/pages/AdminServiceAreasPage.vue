<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import ConfirmActionModal from '../components/ConfirmActionModal.vue'

const areas = ref([])
const city = ref('')
const state = ref('')
const selectedState = ref('')
const addingNewState = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const creating = ref(false)
const editingAreaId = ref(null)
const deletingAreaId = ref(null)
const searchQuery = ref('')
const currentPage = ref(1)
const pendingDeleteArea = ref(null)
const pageSize = 7
const normalized = value => String(value || '').trim().toLowerCase()

const stateGroups = computed(() => {
  const groups = new Map()
  for (const area of areas.value) {
    const key = normalized(area.state)
    const group = groups.get(key) || { state: area.state, cities: [], demand_count: 0, professional_count: 0 }
    group.cities.push(area)
    group.demand_count += area.demand_count
    group.professional_count += area.professional_count
    groups.set(key, group)
  }
  return [...groups.values()]
    .map(group => ({ ...group, cities: group.cities.sort((a, b) => a.city.localeCompare(b.city)) }))
    .sort((a, b) => a.state.localeCompare(b.state))
})
const activeGroup = computed(() => stateGroups.value.find(group => normalized(group.state) === normalized(selectedState.value)) || null)
const filteredCities = computed(() => {
  const query = normalized(searchQuery.value)
  return (activeGroup.value?.cities || []).filter(area => normalized(area.city).includes(query))
})
const pageCount = computed(() => Math.max(1, Math.ceil(filteredCities.value.length / pageSize)))
const visibleCities = computed(() => filteredCities.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const cityDemand = computed(() => [...areas.value].sort((a, b) => b.demand_count - a.demand_count || a.city.localeCompare(b.city)).slice(0, 5))
const maximumDemand = computed(() => Math.max(1, ...cityDemand.value.map(area => area.demand_count)))

watch(selectedState, () => { searchQuery.value = ''; currentPage.value = 1 })
watch(searchQuery, () => { currentPage.value = 1 })
watch(pageCount, lastPage => { if (currentPage.value > lastPage) currentPage.value = lastPage })

function authHeaders(includeJson = false) {
  const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  if (includeJson) headers['Content-Type'] = 'application/json'
  return headers
}

async function loadAreas(preferredState = '') {
  const response = await fetch('/api/admin/service-areas', { headers: authHeaders() })
  const data = await response.json()
  if (!response.ok) throw new Error(data.message || 'Could not load service areas')
  areas.value = data.service_areas
  const wantedState = preferredState || selectedState.value
  const matchingState = stateGroups.value.find(group => normalized(group.state) === normalized(wantedState))
  selectedState.value = matchingState?.state || stateGroups.value[0]?.state || ''
}

function selectState(stateName) {
  selectedState.value = stateName
  state.value = stateName
  city.value = ''
  editingAreaId.value = null
  addingNewState.value = false
  errorMessage.value = ''
}

function startNewState() {
  selectedState.value = ''
  state.value = ''
  city.value = ''
  editingAreaId.value = null
  addingNewState.value = true
  errorMessage.value = ''
  document.querySelector('.area-city-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function saveArea() {
  errorMessage.value = ''
  successMessage.value = ''
  creating.value = true
  const savedState = state.value
  try {
    const isEditing = editingAreaId.value !== null
    const response = await fetch(isEditing ? `/api/admin/service-areas/${editingAreaId.value}` : '/api/admin/service-areas', {
      method: isEditing ? 'PATCH' : 'POST',
      headers: authHeaders(true),
      body: JSON.stringify({ city: city.value, state: state.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not save this city')
    successMessage.value = isEditing ? 'City updated successfully' : `${city.value} was added to ${state.value}`
    city.value = ''
    editingAreaId.value = null
    addingNewState.value = false
    await loadAreas(savedState)
    state.value = selectedState.value
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    creating.value = false
  }
}

function editArea(area) {
  selectedState.value = area.state
  state.value = area.state
  city.value = area.city
  editingAreaId.value = area.id
  addingNewState.value = false
  errorMessage.value = ''
  document.querySelector('.area-city-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function cancelEdit() {
  const wasAddingNewState = addingNewState.value
  city.value = ''
  editingAreaId.value = null
  addingNewState.value = false
  errorMessage.value = ''
  if (wasAddingNewState && stateGroups.value.length) {
    selectState(stateGroups.value[0].state)
  } else {
    state.value = selectedState.value
  }
}

function demandHeight(count) { return `${(count / maximumDemand.value) * 100}%` }

async function deleteArea(area) {
  errorMessage.value = ''
  successMessage.value = ''
  deletingAreaId.value = area.id
  try {
    const response = await fetch(`/api/admin/service-areas/${area.id}`, { method: 'DELETE', headers: authHeaders() })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not delete this city')
    successMessage.value = `${area.city} was removed from the service network`
    await loadAreas(area.state)
    state.value = selectedState.value
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    deletingAreaId.value = null
    pendingDeleteArea.value = null
  }
}

onMounted(async () => {
  try { await loadAreas(); state.value = selectedState.value }
  catch (error) { errorMessage.value = error.message }
})
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="areas" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading"><div><p class="workbench-label">NETWORK / AREAS</p><h1>States first.<br />Cities within.</h1></div><p>Build a clear service network by adding supported cities inside each state. GPS matching uses the normalized city and state.</p></header>

      <section class="area-demand-panel">
        <div class="area-demand-panel__heading"><div><p class="workbench-label">LIVE DEMAND</p><h2>Requests by city</h2></div><p>Demand comes from customer bookings connected to each supported city.</p></div>
        <div v-if="cityDemand.length" class="area-demand-chart"><div class="area-network-summary"><span><strong>{{ stateGroups.length }}</strong> states</span><span><strong>{{ areas.length }}</strong> cities</span><small>Top 5 cities ranked by booking demand</small></div><div class="city-demand-plot"><div class="city-demand-scale" aria-hidden="true"><span>{{ maximumDemand }}</span><span>{{ Math.ceil(maximumDemand / 2) }}</span><span>0</span></div><div class="city-demand-columns" :style="{ '--city-count': cityDemand.length }"><article v-for="(area, index) in cityDemand" :key="area.id"><div class="city-demand-column"><i :style="{ height: demandHeight(area.demand_count) }"><strong>{{ area.demand_count }}</strong></i></div><footer><span>#{{ index + 1 }}</span><b>{{ area.city }}</b><small>{{ area.state }}</small></footer></article></div></div></div>
        <p v-else class="records-empty">Add the first state and city to begin building the network.</p>
      </section>

      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>

      <section class="area-network-manager">
        <header class="area-network-toolbar">
          <div><p class="workbench-label">SERVICE NETWORK</p><h2>{{ areas.length }} cities across {{ stateGroups.length }} states</h2></div>
          <label v-if="stateGroups.length">View state<select v-model="selectedState" @change="selectState(selectedState)"><option v-for="group in stateGroups" :key="group.state" :value="group.state">{{ group.state }} · {{ group.cities.length }} cit{{ group.cities.length === 1 ? 'y' : 'ies' }}</option></select></label>
          <button type="button" @click="startNewState">+ New state</button>
        </header>

        <div class="area-city-workspace">
          <header v-if="activeGroup && !addingNewState"><div><p class="workbench-label">{{ activeGroup.state.toUpperCase() }} / CITIES</p><h2>{{ activeGroup.cities.length }} supported cit{{ activeGroup.cities.length === 1 ? 'y' : 'ies' }}</h2><p>{{ activeGroup.professional_count }} active professional(s) · {{ activeGroup.demand_count }} booking(s)</p></div></header>
          <header v-else><div><p class="workbench-label">NEW STATE</p><h2>Add its first city.</h2><p>The state will appear in the selector after its first supported city is saved.</p></div></header>

          <form class="area-city-form" @submit.prevent="saveArea">
            <label v-if="addingNewState || editingAreaId">State<input v-model.trim="state" placeholder="Example: Karnataka" required /></label>
            <div v-else class="area-form-context"><small>ADDING CITY TO</small><strong>{{ selectedState }}</strong></div>
            <label>City<input v-model.trim="city" placeholder="Example: Bengaluru" required /></label>
            <div class="service-form-actions"><button type="submit" :disabled="creating">{{ creating ? 'Saving…' : editingAreaId ? 'Save changes' : addingNewState ? 'Create state and city' : 'Add city' }}</button><button v-if="editingAreaId || addingNewState" type="button" class="service-form-cancel" :disabled="creating" @click="cancelEdit">Cancel</button></div>
          </form>

          <div v-if="activeGroup && !addingNewState" class="area-city-list">
            <div class="area-city-list-tools"><label class="list-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search cities in this state" aria-label="Search cities" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label><span>{{ filteredCities.length }} result{{ filteredCities.length === 1 ? '' : 's' }}</span></div>
            <article v-for="area in visibleCities" :key="area.id"><div><strong>{{ area.city }}</strong><small>{{ area.professional_count }} active professional(s) · {{ area.demand_count }} booking(s)</small></div><div><button type="button" @click="editArea(area)">Edit</button><button type="button" class="area-delete-button" :disabled="deletingAreaId === area.id" @click="pendingDeleteArea = area">{{ deletingAreaId === area.id ? 'Deleting…' : 'Delete' }}</button></div></article>
            <p v-if="!filteredCities.length">No cities match this search.</p>
            <nav v-if="pageCount > 1" class="area-pagination" aria-label="City pages"><button type="button" :disabled="currentPage === 1" @click="currentPage--">Previous</button><span>{{ currentPage }} / {{ pageCount }}</span><button type="button" :disabled="currentPage === pageCount" @click="currentPage++">Next</button></nav>
          </div>
        </div>
      </section>
    </main>
    <ConfirmActionModal :open="Boolean(pendingDeleteArea)" eyebrow="Service network" :title="`Remove ${pendingDeleteArea?.city || 'this city'}?`" :description="`${pendingDeleteArea?.city || 'This city'} can be removed only when no bookings or active professionals use it.`" confirm-label="Remove city" :busy="deletingAreaId === pendingDeleteArea?.id" danger @confirm="deleteArea(pendingDeleteArea)" @cancel="pendingDeleteArea = null" />
  </div>
</template>
