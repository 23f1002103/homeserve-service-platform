<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const status = ref('checking')
const errorMessage = ref('')
const detectedLocation = ref(null)

function authHeaders(includeJson = false) {
  const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  if (includeJson) headers['Content-Type'] = 'application/json'
  return headers
}

function detectLocation() {
  errorMessage.value = ''
  detectedLocation.value = null

  if (!navigator.geolocation) {
    status.value = 'error'
    errorMessage.value = 'Location detection is not supported by this browser.'
    return
  }

  status.value = 'locating'
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const response = await fetch('/api/professional/detect-service-area', {
          method: 'POST',
          headers: authHeaders(true),
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          }),
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.message || 'Could not check your location')

        detectedLocation.value = data.detected_location
        if (!data.matched_area) {
          status.value = 'unavailable'
          return
        }

        status.value = 'saving'
        sessionStorage.setItem('professional_location_verified', '1')
        await router.replace('/professional/dashboard')
      } catch (error) {
        status.value = 'error'
        errorMessage.value = error.message
      }
    },
    (error) => {
      status.value = 'error'
      errorMessage.value = error.code === error.PERMISSION_DENIED
        ? 'Location permission is required to find bookings in your area.'
        : 'Your current location could not be found. Please try again.'
    },
    { enableHighAccuracy: false, timeout: 10000 },
  )
}

onMounted(detectLocation)
</script>

<template>
  <main class="professional-location-page">
    <RouterLink class="location-brand" to="/">HomeServe</RouterLink>
    <section class="location-card" aria-live="polite">
      <div v-if="status === 'checking' || status === 'locating' || status === 'saving'" class="location-progress">
        <span class="location-pulse" aria-hidden="true"></span>
        <p class="workbench-label">SETTING UP YOUR WORK AREA</p>
        <h1>{{ status === 'saving' ? 'Area found.' : 'Fetching your current location…' }}</h1>
        <p>{{ status === 'saving' ? 'Saving your area and loading matching bookings.' : 'Please allow location access when your browser asks.' }}</p>
      </div>

      <div v-else-if="status === 'unavailable'" class="location-result">
        <p class="workbench-label">CURRENT LOCATION</p>
        <h1>HomeServe is not available here yet.</h1>
        <p>
          We detected <strong>{{ detectedLocation?.city || 'your current area' }}</strong><template v-if="detectedLocation?.pin_code"> — {{ detectedLocation.pin_code }}</template>,
          but the admin has not opened service in this city.
        </p>
        <div class="location-actions">
          <button type="button" @click="detectLocation">Try again</button>
        </div>
      </div>

      <div v-else class="location-result">
        <p class="workbench-label">LOCATION NEEDED</p>
        <h1>We could not set your work area.</h1>
        <p class="location-error" role="alert">{{ errorMessage }}</p>
        <div class="location-actions">
          <button type="button" @click="detectLocation">Try again</button>
        </div>
      </div>
    </section>
  </main>
</template>
