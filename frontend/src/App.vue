<script setup>
import { onUnmounted, ref } from 'vue'
import { RouterView } from 'vue-router'

const activeRequests = ref(0)
const offline = ref(!navigator.onLine)
const connectionRestored = ref(false)
let restoredTimer

function updateNetworkActivity(event) {
  activeRequests.value = event.detail.activeRequests
}

function handleOffline() {
  offline.value = true
  connectionRestored.value = false
  window.clearTimeout(restoredTimer)
}

function handleOnline() {
  const wasOffline = offline.value
  offline.value = false
  if (!wasOffline) return
  connectionRestored.value = true
  restoredTimer = window.setTimeout(() => { connectionRestored.value = false }, 3500)
}

window.addEventListener('homeserve:network-activity', updateNetworkActivity)
window.addEventListener('offline', handleOffline)
window.addEventListener('online', handleOnline)

onUnmounted(() => {
  window.removeEventListener('homeserve:network-activity', updateNetworkActivity)
  window.removeEventListener('offline', handleOffline)
  window.removeEventListener('online', handleOnline)
  window.clearTimeout(restoredTimer)
})
</script>

<template>
  <div v-if="activeRequests" class="global-network-progress" role="progressbar" aria-label="Loading HomeServe data"><span></span></div>
  <Transition name="connection-notice">
    <aside v-if="offline" class="connection-banner is-offline" role="alert"><span></span><div><strong>You’re offline</strong><small>Check your internet connection. HomeServe will reconnect automatically.</small></div></aside>
    <aside v-else-if="connectionRestored" class="connection-banner is-online" role="status"><span>✓</span><div><strong>Back online</strong><small>Your connection has been restored.</small></div></aside>
  </Transition>
  <RouterView />
</template>

