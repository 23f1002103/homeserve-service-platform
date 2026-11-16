<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import ConfirmActionModal from '../components/ConfirmActionModal.vue'
import PageHeading from '../components/PageHeading.vue'

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
const packages = ref([])
const packageName = ref('')
const packageDescription = ref('')
const packageServiceTypeIds = ref([])
const packagePrice = ref('')
const creatingPackage = ref(false)
const updatingPackageId = ref(null)
const visibleServices = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return services.value.filter(service => [service.name, service.description, service.base_price].some(value => String(value || '').toLowerCase().includes(query)))
})

async function loadServices() {
  try {
    const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    const [response, packagesResponse] = await Promise.all([
      fetch('/api/admin/service-types', { headers }),
      fetch('/api/admin/service-packages', { headers }),
    ])
    const [data, packagesData] = await Promise.all([response.json(), packagesResponse.json()])
    if (!response.ok) throw new Error(data.message || 'Could not load services')
    if (!packagesResponse.ok) throw new Error(packagesData.message || 'Could not load packages')
    services.value = data.service_types
    packages.value = packagesData.service_packages
    priceDrafts.value = Object.fromEntries(
      data.service_types.map((service) => [service.id, service.base_price || '']),
    )
  } catch (error) { errorMessage.value = error.message }
}

async function createPackage() {
  errorMessage.value = ''
  successMessage.value = ''
  creatingPackage.value = true
  try {
    const response = await fetch('/api/admin/service-packages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({
        name: packageName.value,
        description: packageDescription.value,
        service_type_ids: packageServiceTypeIds.value.map(Number),
        package_price: packagePrice.value,
      }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not create package')
    packageName.value = ''
    packageDescription.value = ''
    packageServiceTypeIds.value = []
    packagePrice.value = ''
    successMessage.value = 'Service package created successfully'
    await loadServices()
  } catch (error) { errorMessage.value = error.message }
  finally { creatingPackage.value = false }
}

async function togglePackage(servicePackage) {
  updatingPackageId.value = servicePackage.id
  errorMessage.value = ''
  try {
    const response = await fetch(`/api/admin/service-packages/${servicePackage.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ is_active: !servicePackage.is_active }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update package')
    successMessage.value = `${servicePackage.name} ${servicePackage.is_active ? 'deactivated' : 'activated'}`
    await loadServices()
  } catch (error) { errorMessage.value = error.message }
  finally { updatingPackageId.value = null }
}

async function deletePackage(servicePackage) {
  updatingPackageId.value = servicePackage.id
  errorMessage.value = ''
  try {
    const response = await fetch(`/api/admin/service-packages/${servicePackage.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not delete package')
    successMessage.value = `${servicePackage.name} deleted successfully`
    await loadServices()
  } catch (error) { errorMessage.value = error.message }
  finally { updatingPackageId.value = null }
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
      <PageHeading variant="admin" eyebrow="Catalogue" title="Services and packages" description="Manage bookable services, prices and combo offers." />
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
      <section class="service-manager standalone-manager">
        <div class="service-manager__intro"><p class="workbench-label">NEW SERVICE TYPE</p><h2>Add a clear service category.</h2><p>Give it a short description and the minimum price customers can expect.</p></div>
        <form class="service-form" @submit.prevent="createService">
          <label>Service name<input v-model="serviceName" required /></label>
          <label>Short description<textarea v-model="serviceDescription" maxlength="180" rows="3"></textarea><small>{{ serviceDescription.length }}/180 characters</small></label>
          <label>Base price (₹)<input v-model="servicePrice" type="number" min="1" step="0.01" required /></label>
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
      <section class="service-manager package-manager">
        <div class="service-manager__intro"><p class="workbench-label">COMBO PACKAGES</p><h2>Combine services.</h2><p>Select two or more services and set one discounted checkout price.</p></div>
        <form class="service-form" @submit.prevent="createPackage">
          <label>Package name<input v-model.trim="packageName" maxlength="120" required /></label>
          <fieldset class="package-service-picker"><legend>Choose at least two services</legend><label v-for="service in services" :key="service.id"><input v-model="packageServiceTypeIds" type="checkbox" :value="service.id" /><span><strong>{{ service.name }}</strong><small>{{ service.base_price ? `₹${service.base_price}` : 'Price pending' }}</small></span></label></fieldset>
          <label>Description<textarea v-model.trim="packageDescription" maxlength="500" rows="3"></textarea></label>
          <label>Package price (₹)<input v-model="packagePrice" type="number" min="1" step="0.01" required /><small>The regular total is calculated from the selected services.</small></label>
          <button type="submit" :disabled="creatingPackage">{{ creatingPackage ? 'Creating…' : 'Create package' }}</button>
        </form>
        <div class="service-type-list package-list">
          <article v-for="servicePackage in packages" :key="servicePackage.id" class="priced-service-row package-admin-row">
            <span>{{ servicePackage.is_active ? 'LIVE' : 'OFF' }}</span>
            <div class="service-copy"><strong>{{ servicePackage.name }}</strong><small>{{ servicePackage.service_types.map(service => service.name).join(' + ') }}</small><small><s>₹{{ servicePackage.regular_price }}</s> &nbsp; ₹{{ servicePackage.package_price }}</small></div>
            <button type="button" :disabled="updatingPackageId === servicePackage.id" @click="togglePackage(servicePackage)">{{ servicePackage.is_active ? 'Deactivate' : 'Activate' }}</button>
            <button class="service-delete-button" type="button" :disabled="updatingPackageId === servicePackage.id" @click="deletePackage(servicePackage)">Delete</button>
          </article>
          <p v-if="!packages.length">No packages yet. Create the first bundle above.</p>
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
