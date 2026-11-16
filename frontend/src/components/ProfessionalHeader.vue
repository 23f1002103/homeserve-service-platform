<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

defineProps({ current: { type: String, required: true } })
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const menuOpen = ref(false)
let statusTimer
let statusCheckRunning = false
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

function saveStatus(data) {
  const savedUser = JSON.parse(localStorage.getItem('user') || '{}')
  savedUser.approval_status = data.approval_status
  savedUser.block_reason = data.block_reason || null
  localStorage.setItem('user', JSON.stringify(savedUser))
}

async function checkAccountStatus() {
  if (statusCheckRunning || document.visibilityState === 'hidden') return
  statusCheckRunning = true
  try {
    const response = await fetch('/api/professional/status', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    if (!response.ok) return
    const data = await response.json()
    saveStatus(data)
    if (data.approval_status === 'blocked') {
      sessionStorage.removeItem('professional_location_verified')
      await router.replace('/professional/blocked')
    } else if (data.approval_status === 'pending') {
      sessionStorage.removeItem('professional_location_verified')
      await router.replace('/professional/pending')
    }
  } finally {
    statusCheckRunning = false
  }
}

function checkWhenVisible() {
  if (document.visibilityState === 'visible') checkAccountStatus()
}

onMounted(() => {
  checkAccountStatus()
  statusTimer = window.setInterval(checkAccountStatus, 10000)
  window.addEventListener('focus', checkAccountStatus)
  document.addEventListener('visibilitychange', checkWhenVisible)
})

onUnmounted(() => {
  window.clearInterval(statusTimer)
  window.removeEventListener('focus', checkAccountStatus)
  document.removeEventListener('visibilitychange', checkWhenVisible)
})
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
        <RouterLink to="/professional/support" @click="menuOpen = false">Help &amp; support</RouterLink>
        <button type="button" @click="logout">Log out</button>
      </div>
    </div>
  </header>
</template>
