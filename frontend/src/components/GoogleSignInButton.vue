<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  buttonText: {
    type: String,
    default: 'signin_with',
  },
  dividerText: {
    type: String,
    default: 'or sign in with email',
  },
})

const emit = defineEmits(['authenticated', 'error'])
const enabled = ref(false)
const buttonTarget = ref(null)

function loadGoogleLibrary() {
  if (window.google?.accounts?.id) return Promise.resolve()
  if (window.__homeServeGoogleLibrary) return window.__homeServeGoogleLibrary

  window.__homeServeGoogleLibrary = new Promise((resolve, reject) => {
    const existingScript = document.querySelector('script[data-homeserve-google]')
    if (existingScript) {
      existingScript.addEventListener('load', resolve, { once: true })
      existingScript.addEventListener('error', reject, { once: true })
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.dataset.homeserveGoogle = 'true'
    script.addEventListener('load', resolve, { once: true })
    script.addEventListener('error', reject, { once: true })
    document.head.appendChild(script)
  })
  return window.__homeServeGoogleLibrary
}

async function exchangeCredential(response) {
  try {
    const apiResponse = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential }),
    })
    const data = await apiResponse.json()
    if (!apiResponse.ok) throw new Error(data.message || 'Google sign-in failed')
    emit('authenticated', data)
  } catch (error) {
    emit('error', error.message)
  }
}

async function setupGoogleButton() {
  try {
    const response = await fetch('/api/auth/google/config')
    const config = await response.json()
    if (!response.ok || !config.enabled || !config.client_id) return

    enabled.value = true
    await nextTick()
    await loadGoogleLibrary()

    window.google.accounts.id.initialize({
      client_id: config.client_id,
      callback: exchangeCredential,
      use_fedcm_for_prompt: true,
    })
    const width = Math.min(360, buttonTarget.value?.clientWidth || 360)
    window.google.accounts.id.renderButton(buttonTarget.value, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      shape: 'rectangular',
      text: props.buttonText,
      width,
    })
  } catch {
    emit('error', 'Google sign-in is temporarily unavailable')
  }
}

onMounted(setupGoogleButton)
onUnmounted(() => window.google?.accounts?.id?.cancel())
</script>

<template>
  <div v-if="enabled" class="google-auth-section">
    <div ref="buttonTarget" class="google-auth-button"></div>
    <div class="auth-divider"><span>{{ dividerText }}</span></div>
  </div>
</template>
