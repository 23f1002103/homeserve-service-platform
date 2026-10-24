<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CustomerHeader from '../components/CustomerHeader.vue'

const route = useRoute()
const router = useRouter()
const service = ref(null)
const profile = ref(null)
const scheduledFor = ref('')
const serviceAddress = ref('')
const servicePinCode = ref('')
const description = ref('')
const errorMessage = ref('')
const serviceAreaAvailable = ref(true)
const detectingLocation = ref(false)
const currentLocation = ref(null)
const detectedLocation = ref(null)
const matchedServiceArea = ref(null)
const locationMatchMethod = ref(null)
const submitting = ref(false)
const bookingId = ref(null)
const demoPayment = ref(null)
const paymentScreen = ref('ready')
const secondsLeft = ref(300)
const qrCells = Array.from({ length: 169 }, (_, index) => index)
let timerId

const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }

function earliestSchedule() {
  const date = new Date(Date.now() + 60 * 60 * 1000)
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return localDate.toISOString().slice(0, 16)
}

const timerLabel = computed(() => {
  const minutes = Math.floor(secondsLeft.value / 60)
  const seconds = String(secondsLeft.value % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})

function startDemoTimer() {
  clearInterval(timerId)
  secondsLeft.value = 300
  timerId = setInterval(() => {
    secondsLeft.value -= 1
    if (secondsLeft.value <= 0) {
      clearInterval(timerId)
      paymentScreen.value = 'expired'
    }
  }, 1000)
}

function qrCellActive(index) {
  const row = Math.floor(index / 13)
  const column = index % 13
  const finder = (top, left) => {
    const localRow = row - top
    const localColumn = column - left
    if (localRow < 0 || localRow > 4 || localColumn < 0 || localColumn > 4) return false
    return localRow === 0 || localRow === 4 || localColumn === 0 || localColumn === 4 || (localRow === 2 && localColumn === 2)
  }
  return finder(0, 0) || finder(0, 8) || finder(8, 0) || ((row * 7 + column * 3 + row * column) % 5 < 2)
}

async function completeDemoPayment(result) {
  paymentScreen.value = 'processing'
  try {
    const response = await fetch(`/api/customer/bookings/${bookingId.value}/complete-demo-payment`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: demoPayment.value.order_id, result }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Demo payment could not be completed')
    paymentScreen.value = data.payment_status === 'completed' ? 'success' : 'failed'
    clearInterval(timerId)
  } catch (error) {
    errorMessage.value = error.message
    paymentScreen.value = 'ready'
  }
}

function closeDemoPayment() {
  clearInterval(timerId)
  demoPayment.value = null
}

function retryDemoPayment() {
  paymentScreen.value = 'ready'
  startDemoTimer()
}

async function loadBookingPage() {
  try {
    const [servicesResponse, profileResponse] = await Promise.all([
      fetch('/api/customer/services', { headers }),
      fetch('/api/customer/profile', { headers }),
    ])
    const servicesData = await servicesResponse.json()
    const profileData = await profileResponse.json()
    if (!servicesResponse.ok) throw new Error(servicesData.message || 'Could not load service')
    if (!profileResponse.ok) throw new Error(profileData.message || 'Could not load your address')

    service.value = servicesData.services.find((item) => item.id === Number(route.params.serviceId))
    if (!service.value) throw new Error('Service not found')
    serviceAreaAvailable.value = servicesData.service_area_available
    profile.value = profileData.profile
    serviceAddress.value = `${profile.value.address}, ${profile.value.city}, ${profile.value.state} - ${profile.value.pin_code}`
    servicePinCode.value = profile.value.pin_code
    scheduledFor.value = earliestSchedule()
  } catch (error) {
    errorMessage.value = error.message
  }
}

function detectCurrentLocation() {
  errorMessage.value = ''
  currentLocation.value = null
  detectedLocation.value = null
  matchedServiceArea.value = null
  if (!navigator.geolocation) {
    errorMessage.value = 'Current location is not supported by this browser'
    return
  }

  detectingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const latitude = position.coords.latitude
        const longitude = position.coords.longitude
        const response = await fetch('/api/customer/detect-service-area', {
          method: 'POST',
          headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ latitude, longitude }),
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.message || 'Could not verify your location')
        if (!data.matched_area) {
          const place = data.detected_location.city || data.detected_location.pin_code || 'this location'
          throw new Error(`HomeServe is not available in ${place} yet`)
        }

        currentLocation.value = { latitude, longitude }
        detectedLocation.value = data.detected_location
        matchedServiceArea.value = data.matched_area
        locationMatchMethod.value = data.match_method
        servicePinCode.value = data.detected_location.pin_code || data.matched_area.pin_code
        if (data.detected_location.full_address) serviceAddress.value = data.detected_location.full_address.slice(0, 200)
      } catch (error) {
        errorMessage.value = error.message
      } finally {
        detectingLocation.value = false
      }
    },
    () => {
      detectingLocation.value = false
      errorMessage.value = 'Allow location permission so we can verify the service area'
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
  )
}

async function submitBooking() {
  errorMessage.value = ''
  if (!currentLocation.value || !matchedServiceArea.value) {
    errorMessage.value = 'Detect and verify your current location before booking'
    return
  }
  submitting.value = true
  try {
    const response = await fetch('/api/customer/bookings', {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_type_id: service.value.id,
        scheduled_for: scheduledFor.value,
        service_address: serviceAddress.value,
        service_pin_code: servicePinCode.value,
        service_area_id: matchedServiceArea.value.id,
        latitude: currentLocation.value.latitude,
        longitude: currentLocation.value.longitude,
        description: description.value,
      }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not create booking')
    bookingId.value = data.booking_id
    demoPayment.value = data.demo_payment
    paymentScreen.value = 'ready'
    startDemoTimer()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

onMounted(loadBookingPage)
onUnmounted(() => clearInterval(timerId))
</script>

<template>
  <div class="workbench customer-workbench">
    <CustomerHeader current="services" />
    <main class="workbench-content customer-booking-page">
      <RouterLink class="booking-back-link" to="/customer/services">← Back to services</RouterLink>
      <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>

      <section v-if="service" class="booking-checkout">
        <div class="booking-checkout__intro">
          <p class="workbench-label">BOOKING REQUEST</p>
          <h1>Tell us what<br />your home needs.</h1>
          <ol>
            <li class="is-current"><span>01</span><div><strong>Service details</strong><small>Describe the problem</small></div></li>
            <li><span>02</span><div><strong>Professional match</strong><small>After you submit</small></div></li>
            <li><span>03</span><div><strong>Confirmation</strong><small>Track under My bookings</small></div></li>
          </ol>
        </div>

        <form class="booking-form-panel" @submit.prevent="submitBooking">
          <div class="booking-selected-service"><div><small>SELECTED SERVICE</small><h2>{{ service.name }}</h2></div><strong>{{ service.price ? `₹${service.price}` : 'Price pending' }}</strong></div>

          <div v-if="!serviceAreaAvailable" class="booking-area-warning">
            Your profile PIN is outside the current service network. You can continue only if the service address below has an admin-approved PIN code.
          </div>

          <section class="booking-location-check" :class="{ 'is-verified': matchedServiceArea }">
            <div><small>CURRENT SERVICE LOCATION</small><strong v-if="matchedServiceArea">{{ detectedLocation.city || matchedServiceArea.city }}, {{ detectedLocation.state || matchedServiceArea.state }}</strong><strong v-else>Verify where the service is needed</strong><p v-if="matchedServiceArea">Matched with the admin-approved {{ matchedServiceArea.city }} area{{ locationMatchMethod === 'city' ? ' by city' : ' by PIN code' }}.</p><p v-else>We use this only to check availability and give the professional map directions.</p></div>
            <button type="button" :disabled="detectingLocation" @click="detectCurrentLocation">{{ detectingLocation ? 'Detecting…' : matchedServiceArea ? 'Detect again' : 'Use current location' }}</button>
          </section>

          <label>Preferred date and time<input v-model="scheduledFor" type="datetime-local" :min="earliestSchedule()" required /></label>
          <label>Service address<textarea v-model.trim="serviceAddress" rows="3" maxlength="200" required></textarea></label>
          <label>Detected PIN code<input v-model.trim="servicePinCode" inputmode="numeric" maxlength="20" readonly required /><small>The admin-approved area is {{ matchedServiceArea ? `${matchedServiceArea.city} — ${matchedServiceArea.pin_code}` : 'checked after location detection' }}.</small></label>
          <label>What is the problem?<textarea v-model.trim="description" rows="5" maxlength="1000" placeholder="Example: The kitchen tap has been leaking since yesterday…" required></textarea><small>{{ description.length }}/1000</small></label>

          <div class="booking-price-note"><span>Base service price</span><strong>{{ service.price ? `₹${service.price}` : 'Not set' }}</strong><p>Final cost may change only if extra work or materials are approved by you.</p></div>

          <section class="demo-payment-note"><span>DEMO MODE</span><div><strong>HomeServe payment simulator</strong><p>Experience a UPI-style checkout without using real money or banking details.</p></div></section>
          <button class="booking-submit" type="submit" :disabled="submitting || !service.price || !matchedServiceArea">{{ submitting ? 'Preparing payment…' : matchedServiceArea ? `Continue to demo payment · ₹${service.price}` : 'Verify location to continue' }}</button>
        </form>
      </section>

      <div v-if="demoPayment" class="demo-pay-backdrop" role="dialog" aria-modal="true" aria-label="HomeServe demo payment">
        <section class="demo-pay-modal">
          <header><div><span>HS</span><div><strong>HomeServe Pay</strong><small>UPI-style payment simulator</small></div></div><button type="button" aria-label="Close demo payment" @click="closeDemoPayment">×</button></header>

          <template v-if="paymentScreen === 'ready'">
            <div class="demo-pay-warning"><b>DEMO ONLY</b><span>This QR cannot request or transfer real money.</span></div>
            <div class="demo-pay-body">
              <div class="demo-qr-wrap"><div class="demo-qr" aria-label="Decorative demo QR code"><i v-for="cell in qrCells" :key="cell" :class="{ active: qrCellActive(cell) }"></i></div><small>Visual simulation — not scannable</small></div>
              <div class="demo-pay-details"><p>PAYING</p><h2>{{ demoPayment.payee }}</h2><strong>₹{{ demoPayment.amount }}</strong><dl><div><dt>Demo UPI ID</dt><dd>{{ demoPayment.demo_upi_id }}</dd></div><div><dt>Order</dt><dd>{{ demoPayment.order_id }}</dd></div><div><dt>Expires in</dt><dd>{{ timerLabel }}</dd></div></dl></div>
            </div>
            <footer class="demo-pay-actions"><button type="button" class="demo-fail-button" @click="completeDemoPayment('failed')">Simulate failure</button><button type="button" class="demo-success-button" @click="completeDemoPayment('success')">Simulate successful payment</button></footer>
          </template>

          <div v-else-if="paymentScreen === 'processing'" class="demo-payment-result is-processing"><span></span><h2>Processing demo payment…</h2><p>Updating the payment and booking records.</p></div>
          <div v-else-if="paymentScreen === 'success'" class="demo-payment-result is-success"><span>✓</span><p>DEMO PAYMENT SUCCESSFUL</p><h2>Booking confirmed.</h2><p>₹{{ demoPayment.amount }} was simulated successfully. No real money was transferred.</p><button type="button" @click="router.push('/customer/bookings')">View my booking</button></div>
          <div v-else-if="paymentScreen === 'failed'" class="demo-payment-result is-failed"><span>×</span><p>DEMO PAYMENT FAILED</p><h2>No payment was recorded.</h2><p>Use retry to demonstrate the successful payment path.</p><button type="button" @click="retryDemoPayment">Retry demo payment</button></div>
          <div v-else class="demo-payment-result is-failed"><span>!</span><p>DEMO SESSION EXPIRED</p><h2>The timer has ended.</h2><button type="button" @click="retryDemoPayment">Start again</button></div>
        </section>
      </div>
    </main>
  </div>
</template>
