<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import AdminHeader from '../components/AdminHeader.vue'
import ConfirmActionModal from '../components/ConfirmActionModal.vue'

const areas = ref([])
const city = ref('')
const state = ref('')
const pinCode = ref('')
const centerLatitude = ref(null)
const centerLongitude = ref(null)
const radiusKm = ref(15)
const placeSearch = ref('')
const searchingPlace = ref(false)
const mapElement = ref(null)
const selectedState = ref('')
const addingNewState = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const creating = ref(false)
const editingAreaId = ref(null)
const deletingAreaId = ref(null)
const availabilityBusyId = ref(null)
const searchQuery = ref('')
const currentPage = ref(1)
const pendingDeleteArea = ref(null)
const pendingAvailabilityArea = ref(null)
const pageSize = 7
let map
let centerMarker
let radiusCircle
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
watch(radiusKm, updateZoneLayers)

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
  resetZone()
  editingAreaId.value = null
  addingNewState.value = false
  errorMessage.value = ''
}

function startNewState() {
  selectedState.value = ''
  state.value = ''
  city.value = ''
  resetZone()
  editingAreaId.value = null
  addingNewState.value = true
  errorMessage.value = ''
  document.querySelector('.area-city-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function resetZone() {
  pinCode.value = ''
  centerLatitude.value = null
  centerLongitude.value = null
  radiusKm.value = 15
  placeSearch.value = ''
  updateZoneLayers()
}

function updateZoneLayers() {
  if (!map) return
  if (centerMarker) map.removeLayer(centerMarker)
  if (radiusCircle) map.removeLayer(radiusCircle)
  centerMarker = null
  radiusCircle = null
  if (centerLatitude.value === null || centerLongitude.value === null) return
  const centre = [centerLatitude.value, centerLongitude.value]
  centerMarker = L.circleMarker(centre, { radius: 8, color: '#fff', weight: 3, fillColor: '#a55232', fillOpacity: 1 }).addTo(map)
  radiusCircle = L.circle(centre, { radius: Number(radiusKm.value) * 1000, color: '#a55232', weight: 2, fillColor: '#a55232', fillOpacity: 0.12 }).addTo(map)
}

function setZoneCentre(latitude, longitude, shouldZoom = true) {
  centerLatitude.value = Number(Number(latitude).toFixed(6))
  centerLongitude.value = Number(Number(longitude).toFixed(6))
  updateZoneLayers()
  if (shouldZoom && map) map.setView([centerLatitude.value, centerLongitude.value], 11)
}

function initializeMap() {
  if (map || !mapElement.value) return
  map = L.map(mapElement.value, { scrollWheelZoom: false }).setView([20.5937, 78.9629], 5)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)
  map.on('click', event => setZoneCentre(event.latlng.lat, event.latlng.lng, false))
  updateZoneLayers()
}

async function searchForPlace() {
  if (placeSearch.value.trim().length < 2) {
    errorMessage.value = 'Enter a city or place to search'
    return
  }
  searchingPlace.value = true
  errorMessage.value = ''
  try {
    const response = await fetch(`/api/admin/location-search?q=${encodeURIComponent(placeSearch.value.trim())}`, { headers: authHeaders() })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not find that place')
    setZoneCentre(data.location.latitude, data.location.longitude)
    if (!city.value && data.location.city) city.value = data.location.city
    if ((!state.value || addingNewState.value) && data.location.state) state.value = data.location.state
    placeSearch.value = data.location.display_name
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    searchingPlace.value = false
  }
}

async function saveArea() {
  errorMessage.value = ''
  successMessage.value = ''
  creating.value = true
  if (centerLatitude.value === null || centerLongitude.value === null) {
    errorMessage.value = 'Search for a place or click the map to set the service centre'
    creating.value = false
    return
  }
  const savedState = state.value
  try {
    const isEditing = editingAreaId.value !== null
    const response = await fetch(isEditing ? `/api/admin/service-areas/${editingAreaId.value}` : '/api/admin/service-areas', {
      method: isEditing ? 'PATCH' : 'POST',
      headers: authHeaders(true),
      body: JSON.stringify({
        city: city.value,
        state: state.value,
        pin_code: pinCode.value,
        center_latitude: centerLatitude.value,
        center_longitude: centerLongitude.value,
        radius_km: Number(radiusKm.value),
      }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not save this city')
    successMessage.value = isEditing ? 'City updated successfully' : `${city.value} was added to ${state.value}`
    city.value = ''
    resetZone()
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
  pinCode.value = area.pin_code || ''
  centerLatitude.value = area.center_latitude
  centerLongitude.value = area.center_longitude
  radiusKm.value = area.radius_km || 15
  placeSearch.value = `${area.city}, ${area.state}`
  editingAreaId.value = area.id
  addingNewState.value = false
  errorMessage.value = ''
  nextTick(() => {
    updateZoneLayers()
    if (area.has_geo_zone) map?.setView([area.center_latitude, area.center_longitude], 11)
  })
  document.querySelector('.area-city-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function cancelEdit() {
  const wasAddingNewState = addingNewState.value
  city.value = ''
  resetZone()
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

async function updateAvailability(area) {
  errorMessage.value = ''
  successMessage.value = ''
  availabilityBusyId.value = area.id
  const nextActiveState = !area.is_active
  try {
    const response = await fetch(`/api/admin/service-areas/${area.id}/availability`, {
      method: 'PATCH',
      headers: authHeaders(true),
      body: JSON.stringify({ is_active: nextActiveState }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update this city')
    successMessage.value = data.message
    await loadAreas(area.state)
    state.value = selectedState.value
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    availabilityBusyId.value = null
    pendingAvailabilityArea.value = null
  }
}

onMounted(async () => {
  await nextTick()
  initializeMap()
  try { await loadAreas(); state.value = selectedState.value }
  catch (error) { errorMessage.value = error.message }
})
onUnmounted(() => { map?.remove(); map = null })
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="areas" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading"><div><p class="workbench-label">NETWORK / AREAS</p><h1>States first.<br />Zones within.</h1></div><p>Choose a centre and radius for every service area. Customer and professional GPS coordinates are matched against the same zone.</p></header>

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
            <label>PIN code <small>Optional</small><input v-model.trim="pinCode" inputmode="numeric" placeholder="Example: 560001" /></label>
            <section class="area-zone-editor">
              <div class="area-zone-controls">
                <div><p class="workbench-label">MAP SERVICE ZONE</p><h3>Set the centre and reach.</h3><p>Search once or click anywhere on the map, then choose how far HomeServe operates from that point.</p></div>
                <label class="area-place-search">Find a place<div><input v-model.trim="placeSearch" placeholder="Example: Kolkata, West Bengal" @keydown.enter.prevent="searchForPlace" /><button type="button" :disabled="searchingPlace" @click="searchForPlace">{{ searchingPlace ? 'Searching…' : 'Search' }}</button></div></label>
                <label>Service radius <strong>{{ radiusKm }} km</strong><input v-model.number="radiusKm" type="range" min="1" max="100" step="1" /></label>
                <dl><div><dt>Latitude</dt><dd>{{ centerLatitude ?? 'Click map' }}</dd></div><div><dt>Longitude</dt><dd>{{ centerLongitude ?? 'Click map' }}</dd></div></dl>
              </div>
              <div ref="mapElement" class="area-zone-map" aria-label="Click the map to choose the service area centre"></div>
            </section>
            <div class="service-form-actions"><button type="submit" :disabled="creating">{{ creating ? 'Saving…' : editingAreaId ? 'Save changes' : addingNewState ? 'Create state and city' : 'Add city' }}</button><button v-if="editingAreaId || addingNewState" type="button" class="service-form-cancel" :disabled="creating" @click="cancelEdit">Cancel</button></div>
          </form>

          <div v-if="activeGroup && !addingNewState" class="area-city-list">
            <div class="area-city-list-tools"><label class="list-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search cities in this state" aria-label="Search cities" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label><span>{{ filteredCities.length }} result{{ filteredCities.length === 1 ? '' : 's' }}</span></div>
            <article v-for="area in visibleCities" :key="area.id" :class="{ 'is-inactive': !area.is_active }"><div><span class="area-status" :class="area.is_active ? 'is-active' : 'is-paused'">{{ area.is_active ? 'Active' : 'Inactive' }}</span><strong>{{ area.city }}</strong><small>{{ area.professional_count }} connected professional(s) · {{ area.demand_count }} booking(s) · {{ area.has_geo_zone ? `${area.radius_km} km GPS zone` : 'GPS zone not set' }}</small></div><div><button type="button" @click="editArea(area)">Edit</button><button type="button" class="area-availability-button" :disabled="availabilityBusyId === area.id" @click="pendingAvailabilityArea = area">{{ area.is_active ? 'Deactivate' : 'Activate' }}</button><button v-if="area.can_delete" type="button" class="area-delete-button" :disabled="deletingAreaId === area.id" @click="pendingDeleteArea = area">{{ deletingAreaId === area.id ? 'Deleting…' : 'Delete permanently' }}</button></div></article>
            <p v-if="!filteredCities.length">No cities match this search.</p>
            <nav v-if="pageCount > 1" class="area-pagination" aria-label="City pages"><button type="button" :disabled="currentPage === 1" @click="currentPage--">Previous</button><span>{{ currentPage }} / {{ pageCount }}</span><button type="button" :disabled="currentPage === pageCount" @click="currentPage++">Next</button></nav>
          </div>
        </div>
      </section>
    </main>
    <ConfirmActionModal :open="Boolean(pendingAvailabilityArea)" eyebrow="Service availability" :title="`${pendingAvailabilityArea?.is_active ? 'Deactivate' : 'Activate'} ${pendingAvailabilityArea?.city || 'this city'}?`" :description="pendingAvailabilityArea?.is_active ? 'New customer and professional GPS matches will stop here. Existing bookings and history will remain safely stored.' : 'Customers and professionals inside this service zone will be able to match again.'" :confirm-label="pendingAvailabilityArea?.is_active ? 'Deactivate city' : 'Activate city'" :busy="availabilityBusyId === pendingAvailabilityArea?.id" :danger="pendingAvailabilityArea?.is_active" @confirm="updateAvailability(pendingAvailabilityArea)" @cancel="pendingAvailabilityArea = null" />
    <ConfirmActionModal :open="Boolean(pendingDeleteArea)" eyebrow="Permanent deletion" :title="`Delete ${pendingDeleteArea?.city || 'this city'} permanently?`" description="This city has no bookings or connected professionals. Permanent deletion cannot be undone." confirm-label="Delete permanently" :busy="deletingAreaId === pendingDeleteArea?.id" danger @confirm="deleteArea(pendingDeleteArea)" @cancel="pendingDeleteArea = null" />
  </div>
</template>
