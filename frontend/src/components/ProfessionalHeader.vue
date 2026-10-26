<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

defineProps({ current: { type: String, required: true } })
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const menuOpen = ref(false)
const links = [
  { name: 'Overview', path: '/professional/dashboard', key: 'overview' },
  { name: 'My jobs', path: '/professional/jobs', key: 'jobs' },
  { name: 'Earnings', path: '/professional/earnings', key: 'earnings' },
]

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('professional_location_verified')
  router.push('/login')
}
</script>

<template>
  <header class="workbench-bar professional-bar">
    <RouterLink class="workbench-logo" to="/professional/dashboard"><span>HS</span><div><strong>HomeServe</strong><small>Professional field desk</small></div></RouterLink>
    <nav class="workbench-tabs" aria-label="Professional navigation">
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
        <span>{{ (user.username || 'P').charAt(0).toUpperCase() }}</span>
        <div><strong>{{ user.username || 'Professional' }}</strong><small>Professional</small></div>
        <b>⌄</b>
      </button>

      <div v-if="menuOpen" class="profile-menu__panel">
        <p><strong>{{ user.username }}</strong><small>{{ user.email }}</small></p>
        <RouterLink to="/professional/profile" @click="menuOpen = false">My profile</RouterLink>
        <RouterLink to="/" @click="menuOpen = false">HomeServe website</RouterLink>
        <button type="button" @click="logout">Log out</button>
      </div>
    </div>
  </header>
</template>
