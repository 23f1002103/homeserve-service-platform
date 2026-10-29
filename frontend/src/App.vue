<script setup>
import { onUnmounted, ref } from 'vue'
import { RouterView } from 'vue-router'

const activeRequests = ref(0)
const showNetworkLoader = ref(false)
const offline = ref(!navigator.onLine)
const connectionRestored = ref(false)
let restoredTimer
let loaderStartedAt = 0
let loaderTimer
let loaderDelayTimer

const loaderDelay = 300
const minimumLoaderTime = 250

function updateNetworkActivity(event) {
  activeRequests.value = event.detail.activeRequests

  if (activeRequests.value > 0) {
    window.clearTimeout(loaderTimer)
    if (showNetworkLoader.value || loaderDelayTimer) return

    loaderDelayTimer = window.setTimeout(() => {
      loaderDelayTimer = undefined
      if (activeRequests.value <= 0) return
      loaderStartedAt = Date.now()
      showNetworkLoader.value = true
    }, loaderDelay)
    return
  }

  window.clearTimeout(loaderDelayTimer)
  loaderDelayTimer = undefined
  if (!showNetworkLoader.value) return

  const remainingTime = Math.max(0, minimumLoaderTime - (Date.now() - loaderStartedAt))
  loaderTimer = window.setTimeout(() => { showNetworkLoader.value = false }, remainingTime)
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
  window.clearTimeout(loaderTimer)
  window.clearTimeout(loaderDelayTimer)
})
</script>

<template>
  <Transition name="global-loader">
    <div
      v-if="showNetworkLoader"
      class="global-network-loader"
      role="status"
      aria-live="polite"
      aria-label="Loading HomeServe data"
    >
      <div class="global-network-loader__panel">
        <div class="global-network-loader__mark" aria-hidden="true">
          <span class="global-network-loader__orbit"></span>
          <span class="global-network-loader__home">H</span>
        </div>
        <div class="global-network-loader__copy">
          <strong>Loading</strong>
          <small>Just a moment…</small>
        </div>
      </div>
    </div>
  </Transition>
  <Transition name="connection-notice">
    <aside v-if="offline" class="connection-banner is-offline" role="alert"><span></span><div><strong>You’re offline</strong><small>Check your internet connection. HomeServe will reconnect automatically.</small></div></aside>
    <aside v-else-if="connectionRestored" class="connection-banner is-online" role="status"><span>✓</span><div><strong>Back online</strong><small>Your connection has been restored.</small></div></aside>
  </Transition>
  <RouterView />
</template>

