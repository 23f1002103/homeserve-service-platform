<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import ConfirmActionModal from '../components/ConfirmActionModal.vue'

const areas = ref([])
const city = ref('')
const state = ref('')
const pinCode = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const creating = ref(false)
const editingAreaId = ref(null)
const deletingAreaId = ref(null)
const searchQuery = ref('')
const currentPage = ref(1)
const pendingDeleteArea = ref(null)
const pageSize = 8
const filteredAreas = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return areas.value
    .filter(area => [area.city, area.state, area.pin_code].some(value => String(value || '').toLowerCase().includes(query)))
    .sort((first, second) => first.city.localeCompare(second.city) || first.pin_code.localeCompare(second.pin_code))
})
const pageCount = computed(() => Math.max(1, Math.ceil(filteredAreas.value.length / pageSize)))
const paginatedAreas = computed(() => filteredAreas.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const cityDemand = computed(() => {
  const cities = new Map()
  for (const area of areas.value) {
    const key = `${area.city.trim().toLowerCase()}|${area.state.trim().toLowerCase()}`
    const item = cities.get(key) || { city: area.city, state: area.state, demand_count: 0, area_count: 0 }
    item.demand_count += area.demand_count
    item.area_count += 1
    cities.set(key, item)
  }
  return [...cities.values()].sort((first, second) => second.demand_count - first.demand_count || first.city.localeCompare(second.city)).slice(0, 5)
})
const maximumDemand = computed(() => Math.max(1, ...cityDemand.value.map((cityItem) => cityItem.demand_count)))
const cityCount = computed(() => new Set(areas.value.map(area => `${area.city.trim().toLowerCase()}|${area.state.trim().toLowerCase()}`)).size)

watch(searchQuery, () => { currentPage.value = 1 })
watch(pageCount, (lastPage) => {
  if (currentPage.value > lastPage) currentPage.value = lastPage
})

function authHeaders(includeJson = false) {
  const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  if (includeJson) headers['Content-Type'] = 'application/json'
  return headers
}

async function loadAreas() {
  try {
    const response = await fetch('/api/admin/service-areas', { headers: authHeaders() })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load service areas')
    areas.value = data.service_areas
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function createArea() {
  errorMessage.value = ''
  successMessage.value = ''
  creating.value = true
  try {
    const isEditing = editingAreaId.value !== null
    const response = await fetch(isEditing ? `/api/admin/service-areas/${editingAreaId.value}` : '/api/admin/service-areas', {
      method: isEditing ? 'PATCH' : 'POST',
      headers: authHeaders(true),
      body: JSON.stringify({ city: city.value, state: state.value, pin_code: pinCode.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not create service area')
    city.value = ''
    state.value = ''
    pinCode.value = ''
    editingAreaId.value = null
    successMessage.value = isEditing ? 'Service area updated successfully' : 'Service area added successfully'
    await loadAreas()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    creating.value = false
  }
}

function editArea(area) {
  errorMessage.value = ''
  successMessage.value = ''
  editingAreaId.value = area.id
  city.value = area.city
  state.value = area.state
  pinCode.value = area.pin_code
  document.querySelector('.service-manager')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function cancelEdit() {
  editingAreaId.value = null
  city.value = ''
  state.value = ''
  pinCode.value = ''
  errorMessage.value = ''
}

function demandHeight(demandCount) {
  return `${(demandCount / maximumDemand.value) * 100}%`
}

async function deleteArea(area) {
  errorMessage.value = ''
  successMessage.value = ''
  deletingAreaId.value = area.id
  try {
    const response = await fetch(`/api/admin/service-areas/${area.id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not delete service area')
    successMessage.value = `${area.city} (${area.pin_code}) was deleted`
    await loadAreas()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    deletingAreaId.value = null
    pendingDeleteArea.value = null
  }
}

onMounted(loadAreas)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="areas" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading">
        <div><p class="workbench-label">NETWORK / AREAS</p><h1>Choose where<br />HomeServe works.</h1></div>
        <p>Professionals can only select areas created here. Customer locations match by exact PIN first, then by city.</p>
      </header>
      <section class="area-demand-panel">
        <div class="area-demand-panel__heading">
          <div><p class="workbench-label">LIVE DEMAND</p><h2>Requests by service area</h2></div>
          <p>Demand is counted from bookings connected to each admin-approved service area.</p>
        </div>
        <div v-if="cityDemand.length" class="area-demand-chart">
          <div class="area-network-summary"><span><strong>{{ cityCount }}</strong> cities</span><span><strong>{{ areas.length }}</strong> PIN-code areas</span><small>Top 5 cities ranked by booking demand</small></div>
          <div class="city-demand-plot">
            <div class="city-demand-scale" aria-hidden="true"><span>{{ maximumDemand }}</span><span>{{ Math.ceil(maximumDemand / 2) }}</span><span>0</span></div>
            <div class="city-demand-columns" :style="{ '--city-count': cityDemand.length }">
              <article v-for="(cityItem, index) in cityDemand" :key="`${cityItem.city}-${cityItem.state}`">
                <div class="city-demand-column"><i :style="{ height: demandHeight(cityItem.demand_count) }"><strong>{{ cityItem.demand_count }}</strong></i></div>
                <footer><span>#{{ index + 1 }}</span><b>{{ cityItem.city }}</b><small>{{ cityItem.state }} · {{ cityItem.area_count }} PIN area{{ cityItem.area_count === 1 ? '' : 's' }}</small></footer>
              </article>
            </div>
          </div>
        </div>
        <p v-else class="records-empty">Create a service area to begin tracking demand.</p>
      </section>

      <section class="service-manager standalone-manager">
        <p v-if="errorMessage" class="dashboard-alert service-manager-notice">{{ errorMessage }}</p>
        <p v-if="successMessage" class="profile-success service-manager-notice">{{ successMessage }}</p>
        <div class="service-manager__intro">
          <p class="workbench-label">{{ editingAreaId === null ? 'NEW SERVICE AREA' : 'EDIT SERVICE AREA' }}</p><h2>{{ editingAreaId === null ? 'Add one supported location.' : 'Update this location.' }}</h2>
          <p>Enter a real city, state, and PIN code. Professionals see these names, not database IDs.</p>
        </div>
        <form class="service-form" @submit.prevent="createArea">
          <label>City<input v-model.trim="city" placeholder="Example: Bengaluru" required /></label>
          <label>State<input v-model.trim="state" placeholder="Example: Karnataka" required /></label>
          <label>PIN code<input v-model.trim="pinCode" placeholder="Example: 560001" required /></label>
          <div class="service-form-actions">
            <button type="submit" :disabled="creating">{{ creating ? 'Saving…' : editingAreaId === null ? 'Add service area' : 'Save changes' }}</button>
            <button v-if="editingAreaId !== null" type="button" class="service-form-cancel" :disabled="creating" @click="cancelEdit">Cancel</button>
          </div>
        </form>
        <div class="service-type-list area-manager-list">
          <label class="list-search manager-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search city, state or PIN" aria-label="Search service areas" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label>
          <div class="area-list-caption"><span>{{ filteredAreas.length }} matching area{{ filteredAreas.length === 1 ? '' : 's' }}</span><span>Page {{ currentPage }} of {{ pageCount }}</span></div>
          <article v-for="(area, index) in paginatedAreas" :key="area.id">
            <span>{{ String((currentPage - 1) * pageSize + index + 1).padStart(2, '0') }}</span>
            <div><strong>{{ area.city }}, {{ area.state }}</strong><small>{{ area.professional_count }} professional(s) selected this area</small></div>
            <code>{{ area.pin_code }}</code>
            <div class="area-row-actions">
              <button type="button" class="area-edit-button" :disabled="deletingAreaId === area.id" @click="editArea(area)">Edit</button>
              <button type="button" class="area-delete-button" :disabled="deletingAreaId === area.id" @click="pendingDeleteArea = area">
                {{ deletingAreaId === area.id ? 'Deleting…' : 'Delete' }}
              </button>
            </div>
          </article>
          <p v-if="!paginatedAreas.length">{{ searchQuery ? 'No service areas match your search.' : 'No service areas yet. Create the first one above.' }}</p>
          <nav v-if="pageCount > 1" class="area-pagination" aria-label="Service area pages"><button type="button" :disabled="currentPage === 1" @click="currentPage--">Previous</button><span>{{ currentPage }} / {{ pageCount }}</span><button type="button" :disabled="currentPage === pageCount" @click="currentPage++">Next</button></nav>
        </div>
      </section>
    </main>
    <ConfirmActionModal
      :open="Boolean(pendingDeleteArea)"
      eyebrow="Service network"
      :title="`Delete ${pendingDeleteArea?.city || 'this area'}?`"
      :description="`PIN ${pendingDeleteArea?.pin_code || ''} will no longer be available for new professionals or bookings. This cannot be undone.`"
      confirm-label="Delete area"
      :busy="deletingAreaId === pendingDeleteArea?.id"
      danger
      @confirm="deleteArea(pendingDeleteArea)"
      @cancel="pendingDeleteArea = null"
    />
  </div>
</template>
