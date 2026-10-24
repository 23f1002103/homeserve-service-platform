<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'

const customers = ref([])
const errorMessage = ref('')
const searchQuery = ref('')
const visibleCustomers = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  return customers.value.filter(customer => [customer.username, customer.email, customer.phone_number, customer.city, customer.state, customer.pin_code].some(value => String(value || '').toLowerCase().includes(query)))
})

async function loadCustomers() {
  try {
    const response = await fetch('/api/admin/customers', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load customers')
    customers.value = data.customers
  } catch (error) { errorMessage.value = error.message }
}

onMounted(loadCustomers)
</script>

<template>
  <div class="workbench admin-workbench">
    <AdminHeader current="customers" />
    <main class="workbench-content admin-section-page">
      <header class="section-page-heading"><div><p class="workbench-label">PEOPLE / CUSTOMERS</p><h1>The households<br />we serve.</h1></div><p>A clear directory of registered HomeServe customers.</p></header>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
      <label class="list-search standalone-search"><span>⌕</span><input v-model.trim="searchQuery" type="search" placeholder="Search customers or locations" aria-label="Search customers" /><button v-if="searchQuery" type="button" @click="searchQuery = ''">Clear</button></label>
      <section class="admin-records customer-records">
        <article v-for="customer in visibleCustomers" :key="customer.id">
          <span class="list-monogram">{{ customer.username.charAt(0).toUpperCase() }}</span>
          <div class="record-identity"><strong>{{ customer.username }}</strong><small>{{ customer.email }}</small></div>
          <div><small>Phone</small><strong>{{ customer.phone_number || 'Not provided' }}</strong></div>
          <div><small>Location</small><strong>{{ customer.city }}, {{ customer.state }}</strong></div>
          <code>{{ customer.pin_code }}</code>
        </article>
        <p v-if="!visibleCustomers.length && !errorMessage" class="records-empty">{{ searchQuery ? 'No customers match your search.' : 'No customers have registered yet.' }}</p>
      </section>
    </main>
  </div>
</template>
