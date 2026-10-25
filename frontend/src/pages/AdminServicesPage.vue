<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import ConfirmActionModal from '../components/ConfirmActionModal.vue'

const services = ref([])
const serviceName = ref('')
const serviceDescription = ref('')
const servicePrice = ref('')
const priceDrafts = ref({})
const errorMessage = ref('')
const successMessage = ref('')
const creating = ref(false)
const savingPriceId = ref(null)
const deletingServiceId = ref(null)
const searchQuery = ref('')
const pendingDeleteService = ref(null)
const visibleServices = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return services.value.filter(service => [service.name, service.description, service.base_price].some(value => String(value || '').toLowerCase().includes(query)))
})

async function loadServices() {
  try {
    const response = await fetch('/api/admin/service-types', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load services')
    services.value = data.service_types
    priceDrafts.value = Object.fromEntries(
      data.service_types.map((service) => [service.id, service.base_price || '']),
    )
  } catch (error) { errorMessage.value = error.message }
}

async function createService() {
  errorMessage.value = ''
  successMessage.value = ''
  creating.value = true
  try {
    const response = await fetch('/api/admin/service-types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ name: serviceName.value, description: serviceDescription.value, base_price: servicePrice.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not create service')
    serviceName.value = ''
    serviceDescription.value = ''
    servicePrice.value = ''
    successMessage.value = 'Service created successfully'
    await loadServices()
  } catch (error) { errorMessage.value = error.message }
  finally { creating.value = false }
}

async function savePrice(service) {
  errorMessage.value = ''
  successMessage.value = ''
  savingPriceId.value = service.id
  try {
    const response = await fetch(`/api/admin/service-types/${service.id}/price`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ base_price: priceDrafts.value[service.id] }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update price')
    successMessage.value = `${service.name} price updated successfully`
    await loadServices()
  } catch (error) { errorMessage.value = error.message }
  finally { savingPriceId.value = null }
}

async function deleteService(service) {
  errorMessage.value = ''
  successMessage.value = ''
  deletingServiceId.value = service.id
  try {
    const response = await fetch(`/api/admin/service-types/${service.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not delete service')
    successMessage.value = `${service.name} deleted successfully`
    await loadServices()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    deletingServiceId.value = null
    pendingDeleteService.value = null
  }
}

onMounted(loadServices)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="services" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading"><div><p class="workbench-label">CATALOGUE / SERVICES</p><h1>Define what<br />HomeServe offers.</h1></div><p>These service names appear in professional registration and future customer booking.</p></header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
      <section class="service-manager standalone-manager">
        <div class="service-manager__intro"><p class="workbench-label">NEW SERVICE TYPE</p><h2>Add a clear service category.</h2><p>Give it a short description and the minimum price customers can expect.</p></div>
        <form class="service-form" @submit.prevent="createService">
          <label>Service name<input v-model="serviceName" placeholder="Example: Plumbing" required /></label>
          <label>Short description<textarea v-model="serviceDescription" maxlength="180" rows="3" placeholder="Example: Leak repairs, pipe fitting and tap replacement"></textarea><small>{{ serviceDescription.length }}/180 characters</small></label>
          <label>Base price (₹)<input v-model="servicePrice" type="number" min="1" step="0.01" placeholder="Example: 499" required /></label>
          <button type="submit" :disabled="creating">{{ creating ? 'Creating…' : 'Add service type' }}</button>
        </form>
        <div class="service-type-list">
          <label class="list-search manager-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search service types" aria-label="Search service types" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label>
          <article v-for="(service, index) in visibleServices" :key="service.id" class="priced-service-row">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="service-copy"><strong>{{ service.name }}</strong><small>{{ service.description || 'No description added' }}</small></div>
            <div class="service-price-editor">
              <span>₹</span><input v-model="priceDrafts[service.id]" type="number" min="1" step="0.01" aria-label="Base price" />
              <button type="button" :disabled="savingPriceId === service.id" @click="savePrice(service)">{{ savingPriceId === service.id ? 'Saving…' : 'Save price' }}</button>
            </div>
            <button class="service-delete-button" type="button" :disabled="deletingServiceId === service.id" @click="pendingDeleteService = service">{{ deletingServiceId === service.id ? 'Deleting…' : 'Delete' }}</button>
          </article>
          <p v-if="!visibleServices.length">{{ searchQuery ? 'No services match your search.' : 'No service types yet. Create the first one above.' }}</p>
        </div>
      </section>
    </main>
    <ConfirmActionModal
      :open="Boolean(pendingDeleteService)"
      eyebrow="Service catalogue"
      :title="`Delete ${pendingDeleteService?.name || 'this service'}?`"
      description="It will disappear from customer booking and professional registration. Services already used by a professional or booking remain protected by the backend."
      confirm-label="Delete service"
      :busy="deletingServiceId === pendingDeleteService?.id"
      danger
      @confirm="deleteService(pendingDeleteService)"
      @cancel="pendingDeleteService = null"
    />
  </div>
</template>
