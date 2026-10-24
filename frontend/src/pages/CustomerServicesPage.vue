<script setup>
import { computed, onMounted, ref } from 'vue'
import CustomerHeader from '../components/CustomerHeader.vue'
const services = ref([])
const area = ref(null)
const serviceAreaAvailable = ref(true)
const errorMessage = ref('')
const searchQuery = ref('')
const visibleServices = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return services.value.filter(service => [service.name, service.description, service.price].some(value => String(value || '').toLowerCase().includes(query)))
})
async function loadServices() {
  try {
    const response = await fetch('/api/customer/services', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load services')
    services.value = data.services
    area.value = data.customer_area
    serviceAreaAvailable.value = data.service_area_available
  } catch (error) { errorMessage.value = error.message }
}
onMounted(loadServices)
</script>

<template>
  <div class="workbench customer-workbench"><CustomerHeader current="services" /><main class="workbench-content role-section-page customer-services-page">
    <header class="role-section-heading"><div><p class="workbench-label">BOOK HOME CARE</p><h1>What needs<br />attention?</h1></div><p>Choose one service to open a short booking form. You will review everything before submitting.</p></header>
    <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>

    <section v-if="area" class="customer-area-strip" :class="{ 'is-unavailable': !serviceAreaAvailable }">
      <div><small>SERVICE LOCATION</small><strong>{{ area.city }} · {{ area.pin_code }}</strong></div>
      <p>{{ serviceAreaAvailable ? 'HomeServe professionals are available in this area.' : 'HomeServe has not opened service in this PIN code yet.' }}</p>
    </section>

    <label class="list-search standalone-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search household services" aria-label="Search services" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label>

    <section class="customer-service-grid">
      <article v-for="(service, index) in visibleServices" :key="service.id">
        <div class="service-card-number">{{ String(index + 1).padStart(2, '0') }}</div>
        <div class="service-card-copy"><p class="workbench-label">HOME SERVICE</p><h2>{{ service.name }}</h2><p>{{ service.description || 'Professional household assistance for your home.' }}</p></div>
        <div class="service-card-footer"><span><small>STARTING FROM</small><strong>{{ service.price ? `₹${ service.price }` : 'Price pending' }}</strong></span><RouterLink v-if="service.price" :to="`/customer/book/${service.id}`">Book service <b>→</b></RouterLink><button v-else disabled>Price pending</button></div>
      </article>
      <p v-if="!visibleServices.length && !errorMessage" class="records-empty">{{ searchQuery ? 'No services match your search.' : 'The admin has not added any services yet.' }}</p>
    </section>
  </main></div>
</template>
