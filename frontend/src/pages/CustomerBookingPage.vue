<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ActionNoticeModal from '../components/ActionNoticeModal.vue'
import CustomerHeader from '../components/CustomerHeader.vue'
import demoQrImage from '../assets/demo-payment-qr.svg'

const route = useRoute()
const router = useRouter()
const service = ref(null)
const profile = ref(null)
const profileRequired = ref(false)
const scheduledFor = ref('')
const serviceAddress = ref('')
const servicePinCode = ref('')
const serviceCity = ref('')
const serviceState = ref('')
const description = ref('')
const errorMessage = ref('')
const serviceAreaAvailable = ref(true)
const locationMethod = ref('gps')
const detectingLocation = ref(false)
const verifyingManualLocation = ref(false)
const currentLocation = ref(null)
const detectedLocation = ref(null)
const matchedServiceArea = ref(null)
const locationMatchMethod = ref(null)
const manualAreaUnavailable = ref(false)
const manualUnavailableMessage = ref('')
const bookingFor = ref('self')
const recipientName = ref('')
const recipientPhone = ref('')
const submitting = ref(false)
const bookingId = ref(null)
const demoPayment = ref(null)
const paymentScreen = ref('ready')
const paymentMethod = ref('qr')
const demoUpiAddress = ref('')
const secondsLeft = ref(300)
let timerId

const resumeBookingId = computed(() => {
  const value = Number(route.query.resume)
  return Number.isInteger(value) && value > 0 ? value : null
})

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
  if (resumeBookingId.value) router.push('/customer/bookings')
}

function retryDemoPayment() {
  paymentScreen.value = 'ready'
  paymentMethod.value = 'qr'
  demoUpiAddress.value = ''
  startDemoTimer()
}

async function resumeDemoPayment() {
  const response = await fetch(`/api/customer/bookings/${resumeBookingId.value}/resume-demo-payment`, {
    method: 'POST',
    headers,
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.message || 'Could not reopen this payment')

  bookingId.value = data.booking_id
  demoPayment.value = data.demo_payment
  paymentScreen.value = 'ready'
  paymentMethod.value = 'qr'
  demoUpiAddress.value = ''
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
    if (profile.value.profile_complete === false) {
      profileRequired.value = true
      return
    }
    serviceAddress.value = `${profile.value.address}, ${profile.value.city}, ${profile.value.state} - ${profile.value.pin_code}`
    servicePinCode.value = profile.value.pin_code
    serviceCity.value = profile.value.city
    serviceState.value = profile.value.state
    scheduledFor.value = earliestSchedule()
    if (resumeBookingId.value) await resumeDemoPayment()
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
          body: JSON.stringify({ latitude, longitude, accuracy: position.coords.accuracy }),
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
        serviceCity.value = data.detected_location.city || data.matched_area.city
        serviceState.value = data.detected_location.state || data.matched_area.state
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

function chooseLocationMethod(method) {
  locationMethod.value = method
  currentLocation.value = null
  detectedLocation.value = null
  matchedServiceArea.value = null
  locationMatchMethod.value = null
  errorMessage.value = ''
  if (method === 'gps') {
    bookingFor.value = 'self'
    recipientName.value = ''
    recipientPhone.value = ''
  }
  if (method === 'manual' && profile.value) {
    serviceAddress.value = `${profile.value.address}, ${profile.value.city}, ${profile.value.state}`
    servicePinCode.value = profile.value.pin_code
    serviceCity.value = profile.value.city
    serviceState.value = profile.value.state
  }
}

async function verifyManualLocation() {
  errorMessage.value = ''
  matchedServiceArea.value = null
  if (!serviceAddress.value || !serviceCity.value || !serviceState.value) {
    errorMessage.value = 'Enter the complete service address, city, and state'
    return
  }

  verifyingManualLocation.value = true
  try {
    const response = await fetch('/api/customer/verify-service-area', {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        city: serviceCity.value,
        state: serviceState.value,
        pin_code: servicePinCode.value,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      if (response.status === 404) {
        manualUnavailableMessage.value = data.message
        manualAreaUnavailable.value = true
        return
      }
      throw new Error(data.message || 'Could not verify this address')
    }

    matchedServiceArea.value = data.matched_area
    locationMatchMethod.value = data.match_method
    detectedLocation.value = {
      city: data.matched_area.city,
      state: data.matched_area.state,
      pin_code: servicePinCode.value,
      full_address: serviceAddress.value,
    }
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    verifyingManualLocation.value = false
  }
}

function completeProfile() {
  router.push({
    name: 'customer-profile',
    query: { complete: '1', reason: 'booking', next: route.fullPath },
  })
}

async function submitBooking() {
  errorMessage.value = ''
  if (!matchedServiceArea.value) {
    errorMessage.value = locationMethod.value === 'manual'
      ? 'Verify the manual service address before booking'
      : 'Detect and verify your current location before booking'
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
        service_city: serviceCity.value,
        service_state: serviceState.value,
        service_area_id: matchedServiceArea.value.id,
        latitude: currentLocation.value?.latitude,
        longitude: currentLocation.value?.longitude,
        description: description.value,
        booking_for: bookingFor.value,
        recipient_name: bookingFor.value === 'other' ? recipientName.value : null,
        recipient_phone: bookingFor.value === 'other' ? recipientPhone.value : null,
      }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not create booking')
    bookingId.value = data.booking_id
    demoPayment.value = data.demo_payment
    paymentScreen.value = 'ready'
    paymentMethod.value = 'qr'
    demoUpiAddress.value = ''
    startDemoTimer()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

watch([serviceAddress, serviceCity, serviceState, servicePinCode], () => {
  if (locationMethod.value === 'manual' && matchedServiceArea.value) {
    matchedServiceArea.value = null
    detectedLocation.value = null
    locationMatchMethod.value = null
  }
})

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
          <div class="booking-intro-summary">
            <small>YOU'RE BOOKING</small>
            <strong>{{ service.name }}</strong>
            <p>Share the location and problem details. We’ll handle the professional match and keep every update in My bookings.</p>
          </div>
        </div>

        <form class="booking-form-panel" @submit.prevent="submitBooking">
          <div class="booking-selected-service"><div><small>SELECTED SERVICE</small><h2>{{ service.name }}</h2></div><strong>{{ service.price ? `₹${service.price}` : 'Price pending' }}</strong></div>

          <section v-if="profile" class="booking-contact-summary">
            <div><small>BOOKING CONTACT</small><strong>{{ profile.username }}</strong><p>{{ profile.phone_number }} · {{ profile.city }}</p></div>
            <RouterLink to="/customer/profile">Edit profile</RouterLink>
          </section>

          <div v-if="!serviceAreaAvailable" class="booking-area-warning">
            Your profile city is outside the current service network. You can continue only if the service address below is in an admin-approved city.
          </div>

          <div class="booking-location-methods" role="group" aria-label="Choose how to provide the service location">
            <button type="button" :class="{ 'is-active': locationMethod === 'gps' }" @click="chooseLocationMethod('gps')"><strong>Use current location</strong><small>Detect with GPS</small></button>
            <button type="button" :class="{ 'is-active': locationMethod === 'manual' }" @click="chooseLocationMethod('manual')"><strong>Enter address manually</strong><small>Verify city and state</small></button>
          </div>

          <section v-if="locationMethod === 'gps'" class="booking-location-check" :class="{ 'is-verified': matchedServiceArea }">
            <div><small>CURRENT SERVICE LOCATION</small><strong v-if="matchedServiceArea">{{ detectedLocation.city || matchedServiceArea.city }}, {{ detectedLocation.state || matchedServiceArea.state }}</strong><strong v-else>Verify where the service is needed</strong><p v-if="matchedServiceArea">Inside the admin-approved {{ matchedServiceArea.city }} service zone.</p><p v-else>We use this only to check availability and give the professional map directions.</p></div>
            <button type="button" :disabled="detectingLocation" @click="detectCurrentLocation">{{ detectingLocation ? 'Detecting…' : matchedServiceArea ? 'Detect again' : 'Use current location' }}</button>
          </section>

          <label>Preferred date and time<input v-model="scheduledFor" type="datetime-local" :min="earliestSchedule()" required /></label>
          <label>Service address<textarea v-model.trim="serviceAddress" rows="3" maxlength="200" :placeholder="locationMethod === 'manual' ? 'House number, street, locality, city and state' : ''" required></textarea></label>
          <div class="booking-location-fields">
            <label>City<input v-model.trim="serviceCity" maxlength="100" :readonly="locationMethod === 'gps'" required /></label>
            <label>State<input v-model.trim="serviceState" maxlength="100" :readonly="locationMethod === 'gps'" required /></label>
          </div>
          <label>{{ locationMethod === 'manual' ? 'Service address PIN code' : 'Detected PIN code' }}<input v-model.trim="servicePinCode" inputmode="numeric" maxlength="20" :readonly="locationMethod === 'gps'" /><small>GPS locations are checked against the administrator's service radius. The PIN code is retained for the exact address.</small></label>

          <section v-if="locationMethod === 'manual'" class="booking-location-check manual-location-check" :class="{ 'is-verified': matchedServiceArea }">
            <div><small>MANUAL SERVICE LOCATION</small><strong v-if="matchedServiceArea">Address verified for {{ matchedServiceArea.city }}</strong><strong v-else>Check service availability</strong><p v-if="matchedServiceArea">{{ matchedServiceArea.city }}, {{ matchedServiceArea.state }} is an admin-approved city.</p><p v-else>We will compare the city and state with the administrator's service areas.</p></div>
            <button type="button" :disabled="verifyingManualLocation" @click="verifyManualLocation">{{ verifyingManualLocation ? 'Checking…' : matchedServiceArea ? 'Verified ✓' : 'Verify address' }}</button>
          </section>

          <section v-if="locationMethod === 'manual'" class="booking-recipient-panel">
            <div class="booking-recipient-heading"><small>WHO IS THIS SERVICE FOR?</small><strong>Choose the person at this address.</strong><p>You will pay for and track the booking from your account.</p></div>
            <div class="booking-recipient-options" role="radiogroup" aria-label="Choose who the booking is for">
              <label :class="{ 'is-active': bookingFor === 'self' }"><input v-model="bookingFor" type="radio" value="self" /><span><strong>Book for myself</strong><small>Use my account contact details</small></span></label>
              <label :class="{ 'is-active': bookingFor === 'other' }"><input v-model="bookingFor" type="radio" value="other" /><span><strong>Book for someone else</strong><small>Share the recipient's contact after acceptance</small></span></label>
            </div>
            <div v-if="bookingFor === 'other'" class="booking-recipient-fields">
              <label>Recipient name<input v-model.trim="recipientName" maxlength="100" autocomplete="name" required /></label>
              <label>Recipient phone<input v-model.trim="recipientPhone" type="tel" minlength="7" maxlength="20" autocomplete="tel" required /></label>
            </div>
          </section>
          <label>What is the problem?<textarea v-model.trim="description" rows="5" maxlength="1000" placeholder="Example: The kitchen tap has been leaking since yesterday…" required></textarea><small>{{ description.length }}/1000</small></label>

          <div class="booking-price-note"><span>Base service price</span><strong>{{ service.price ? `₹${service.price}` : 'Not set' }}</strong><p>Final cost may change only if extra work or materials are approved by you.</p></div>

          <section class="demo-payment-note"><span>DEMO MODE</span><div><strong>HomeServe payment simulator</strong><p>Experience a UPI-style checkout without using real money or banking details.</p></div></section>
          <button class="booking-submit" type="submit" :disabled="submitting || !service.price || !matchedServiceArea">{{ submitting ? 'Preparing payment…' : matchedServiceArea ? `Continue to demo payment · ₹${service.price}` : 'Verify location to continue' }}</button>
        </form>
      </section>

      <div v-if="demoPayment" class="demo-pay-backdrop" role="dialog" aria-modal="true" aria-label="HomeServe demo payment">
        <section class="demo-pay-modal">
          <template v-if="paymentScreen === 'ready'">
            <div class="gateway-checkout-shell">
              <aside class="gateway-order-summary">
                <div class="gateway-brand"><span>HS</span><div><strong>HomeServe</strong><small>Secure Checkout</small></div></div>
                <div class="gateway-order-copy"><small>PAYMENT FOR</small><strong>{{ service?.name || 'Home service' }}</strong><span>Booking #{{ bookingId }}</span></div>
                <div class="gateway-amount"><small>AMOUNT PAYABLE</small><strong><sup>₹</sup>{{ demoPayment.amount }}</strong></div>
                <dl><div><dt>Order ID</dt><dd>{{ demoPayment.order_id }}</dd></div><div><dt>Customer</dt><dd>{{ profile?.username }}</dd></div></dl>
                <div class="gateway-secure-note"><span>⌾</span><div><strong>Secured checkout</strong><small>256-bit style payment experience</small></div></div>
                <p><b>TEST MODE</b> No real money will be transferred.</p>
              </aside>

              <section class="gateway-payment-panel">
                <header><div><small>PAYMENT OPTIONS</small><strong>Pay ₹{{ demoPayment.amount }}</strong></div><button type="button" aria-label="Close demo payment" @click="closeDemoPayment">×</button></header>
                <div class="gateway-demo-warning"><b>DEMO</b><span>Use either option below to simulate a UPI payment.</span><time>{{ timerLabel }}</time></div>
                <div class="gateway-payment-workspace">
                  <nav aria-label="Demo payment methods"><button type="button" :class="{ active: paymentMethod === 'qr' }" @click="paymentMethod = 'qr'"><span>▦</span><div><strong>QR Code</strong><small>Scan using any UPI app</small></div><b>›</b></button><button type="button" :class="{ active: paymentMethod === 'upi' }" @click="paymentMethod = 'upi'"><span>UPI</span><div><strong>UPI ID</strong><small>Pay using your VPA</small></div><b>›</b></button></nav>

                  <div v-if="paymentMethod === 'qr'" class="gateway-method-content gateway-qr-content">
                    <div class="gateway-method-heading"><h2>Scan QR to pay</h2><p>Open any UPI app and scan this demo code</p></div>
                    <div class="demo-qr-wrap"><img class="demo-qr" :src="demoQrImage" alt="Decorative fake QR code for the HomeServe payment demo" /><small>DEMO QR · NOT SCANNABLE</small></div>
                    <div class="gateway-upi-apps"><span>G Pay</span><span>PhonePe</span><span>Paytm</span><span>BHIM</span></div>
                    <button type="button" class="gateway-primary-action" @click="completeDemoPayment('success')">I have completed the payment</button>
                  </div>

                  <div v-else class="gateway-method-content gateway-upi-content">
                    <div class="gateway-method-heading"><h2>Pay using UPI ID</h2><p>Enter a demo VPA to continue</p></div>
                    <label>UPI ID<input v-model.trim="demoUpiAddress" type="text" placeholder="name@bank" autocomplete="off" /><small>Example: customer@upi</small></label>
                    <div class="gateway-vpa-info"><span>✓</span><p>This is a simulation. No collect request will be sent to this UPI ID.</p></div>
                    <button type="button" class="gateway-primary-action" :disabled="!demoUpiAddress" @click="completeDemoPayment('success')">Verify and pay ₹{{ demoPayment.amount }}</button>
                  </div>
                </div>
                <footer><span>🔒 Payments secured by HomeServe Demo</span><button type="button" @click="completeDemoPayment('failed')">Simulate failed payment</button></footer>
              </section>
            </div>
          </template>

          <div v-else-if="paymentScreen === 'processing'" class="demo-payment-result is-processing"><span></span><h2>Processing demo payment…</h2><p>Updating the payment and booking records.</p></div>
          <div v-else-if="paymentScreen === 'success'" class="demo-payment-result is-success"><span>✓</span><p>BOOKING #{{ bookingId }} CONFIRMED</p><h2>Your request is now live.</h2><p>The demo payment of ₹{{ demoPayment.amount }} was recorded. We’ll notify you when a professional accepts the job.</p><button type="button" @click="router.push('/customer/bookings')">Track my booking</button></div>
          <div v-else-if="paymentScreen === 'failed'" class="demo-payment-result is-failed"><span>×</span><p>DEMO PAYMENT FAILED</p><h2>No payment was recorded.</h2><p>Use retry to demonstrate the successful payment path.</p><button type="button" @click="retryDemoPayment">Retry demo payment</button></div>
          <div v-else class="demo-payment-result is-failed"><span>!</span><p>DEMO SESSION EXPIRED</p><h2>The timer has ended.</h2><button type="button" @click="retryDemoPayment">Start again</button></div>
        </section>
      </div>

      <ActionNoticeModal
        :open="profileRequired"
        eyebrow="Before you book"
        title="Tell us where we can reach you."
        description="Your Google sign-in is complete. Add your phone number and home address once so we can create the booking and share the correct location with your assigned professional."
        primary-label="Complete my profile"
        secondary-label="Browse services"
        symbol="⌂"
        @primary="completeProfile"
        @secondary="router.push('/customer/services')"
      />
      <ActionNoticeModal
        :open="manualAreaUnavailable"
        eyebrow="Service area check"
        title="HomeServe is not available at this address yet."
        :description="manualUnavailableMessage || 'The city and state do not match an admin-approved service area.'"
        primary-label="Edit address"
        secondary-label="Browse services"
        symbol="⌖"
        @primary="manualAreaUnavailable = false"
        @secondary="router.push('/customer/services')"
      />
    </main>
  </div>
</template>
