<script setup>
import { useRouter } from 'vue-router'

defineProps({ current: { type: String, required: true } })

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')

const links = [
  { name: 'Overview', path: '/admin/dashboard', key: 'overview' },
  { name: 'Professionals', path: '/admin/professionals', key: 'professionals' },
  { name: 'Customers', path: '/admin/customers', key: 'customers' },
  { name: 'Services', path: '/admin/services', key: 'services' },
  { name: 'Areas', path: '/admin/service-areas', key: 'areas' },
  { name: 'Requests', path: '/admin/requests', key: 'requests' },
  { name: 'Revenue', path: '/admin/revenue', key: 'revenue' },
]

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<template>
  <header class="workbench-bar admin-page-header">
    <RouterLink class="workbench-logo" to="/admin/dashboard">
      <span>HS</span><div><strong>HomeServe</strong><small>Operations desk</small></div>
    </RouterLink>

    <nav class="workbench-tabs" aria-label="Admin navigation">
      <RouterLink
        v-for="link in links"
        :key="link.key"
        :to="link.path"
        :class="{ 'is-current': current === link.key }"
      >
        {{ link.name }}
      </RouterLink>
    </nav>

    <div class="workbench-account">
      <span>{{ (user.username || 'A').charAt(0).toUpperCase() }}</span>
      <button type="button" @click="logout">Sign out</button>
    </div>
  </header>
</template>
