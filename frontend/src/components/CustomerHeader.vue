<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

defineProps({ current: { type: String, required: true } })
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const menuOpen = ref(false)
const links = [
  { name: 'Home', path: '/customer/dashboard', key: 'overview' },
  { name: 'Services', path: '/customer/services', key: 'services' },
  { name: 'My bookings', path: '/customer/bookings', key: 'bookings' },
]

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<template>
  <header class="workbench-bar customer-bar">
    <RouterLink class="workbench-logo" to="/customer/dashboard"><span>HS</span><div><strong>HomeServe</strong><small>Care for your home</small></div></RouterLink>
    <nav class="workbench-tabs" aria-label="Customer navigation">
      <RouterLink v-for="link in links" :key="link.key" :to="link.path" :class="{ 'is-current': current === link.key }">{{ link.name }}</RouterLink>
    </nav>
    <div class="profile-menu">
      <button
        class="profile-menu__trigger"
        type="button"
        :aria-expanded="menuOpen"
        aria-label="Open profile menu"
        @click="menuOpen = !menuOpen"
      >
        <span>{{ (user.username || 'C').charAt(0).toUpperCase() }}</span>
        <div><strong>{{ user.username || 'Customer' }}</strong><small>Customer</small></div>
        <b>⌄</b>
      </button>

      <div v-if="menuOpen" class="profile-menu__panel">
        <p><strong>{{ user.username }}</strong><small>{{ user.email }}</small></p>
        <RouterLink to="/customer/profile" @click="menuOpen = false">My profile</RouterLink>
        <RouterLink to="/" @click="menuOpen = false">HomeServe website</RouterLink>
        <button type="button" @click="logout">Log out</button>
      </div>
    </div>
  </header>
</template>
