<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import GoogleSignInButton from '../components/GoogleSignInButton.vue'

const router = useRouter()
const errorMessage = ref('')
const submitting = ref(false)
const serviceTypes = ref([])
const servicesLoading = ref(false)

async function finishGoogleRegistration(data) {
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))
  await router.push('/customer/dashboard')
}

function showGoogleError(message) {
  errorMessage.value = message
}

const form = reactive({
  username: '',
  email: '',
  password: '',
  role: 'customer',
  phone_number: '',
  address: '',
  city: '',
  state: '',
  pin_code: '',
  service_type_id: '',
  experience_years: '',
})

async function loadServiceTypes() {
  servicesLoading.value = true
  try {
    const response = await fetch('/api/service-types')
    const data = await response.json()
    if (!response.ok) throw new Error('Could not load service types')
    serviceTypes.value = data.service_types
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    servicesLoading.value = false
  }
}

async function register() {
  errorMessage.value = ''
  submitting.value = true

  const payload = { ...form }
  if (form.role === 'professional') {
    payload.service_type_id = Number(form.service_type_id)
    payload.experience_years = form.experience_years === '' ? null : Number(form.experience_years)
  } else {
    delete payload.service_type_id
    delete payload.experience_years
  }

  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Registration failed')
    }

    if (form.role === 'professional') {
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      await router.push('/professional/pending')
    } else {
      await router.push({ name: 'login', query: { registered: '1' } })
    }
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

onMounted(loadServiceTypes)
</script>

<template>
  <main class="auth-page auth-page--wide">
    <RouterLink class="auth-brand" to="/">HomeServe</RouterLink>

    <section class="auth-card" aria-labelledby="register-title">
      <p class="eyebrow">Join HomeServe</p>
      <h1 id="register-title">Create your account</h1>

      <GoogleSignInButton
        v-if="form.role === 'customer'"
        button-text="signup_with"
        divider-text="or register with email"
        @authenticated="finishGoogleRegistration"
        @error="showGoogleError"
      />

      <form class="register-grid" @submit.prevent="register">
        <label>
          Username
          <input v-model="form.username" autocomplete="username" required />
        </label>
        <label>
          Email
          <input v-model="form.email" type="email" autocomplete="email" required />
        </label>
        <label>
          Password
          <input v-model="form.password" type="password" minlength="8" autocomplete="new-password" required />
        </label>
        <label>
          Account type
          <select v-model="form.role">
            <option value="customer">Customer</option>
            <option value="professional">Professional</option>
          </select>
        </label>
        <label>
          Phone number
          <input v-model="form.phone_number" type="tel" autocomplete="tel" :required="form.role === 'customer'" />
        </label>
        <label>
          PIN code
          <input v-model="form.pin_code" autocomplete="postal-code" required />
        </label>
        <label class="form-wide">
          Address
          <input v-model="form.address" autocomplete="street-address" required />
        </label>
        <label>
          City
          <input v-model="form.city" autocomplete="address-level2" required />
        </label>
        <label>
          State
          <input v-model="form.state" autocomplete="address-level1" required />
        </label>

        <template v-if="form.role === 'professional'">
          <label>
            Service type
            <select v-model="form.service_type_id" required>
              <option value="" disabled>
                {{ servicesLoading ? 'Loading services…' : 'Choose your service' }}
              </option>
              <option v-for="service in serviceTypes" :key="service.id" :value="service.id">
                {{ service.name }}
              </option>
            </select>
          </label>
          <label>
            Years of experience
            <input v-model="form.experience_years" type="number" min="0" />
          </label>
          <p class="professional-note form-wide">
            <template v-if="serviceTypes.length">
              Professional accounts require admin approval before receiving work.
            </template>
            <template v-else-if="!servicesLoading">
              No service types are available yet. An admin must create one first.
            </template>
          </p>
        </template>

        <p v-if="errorMessage" class="form-error form-wide" role="alert">{{ errorMessage }}</p>
        <button
          class="button auth-submit form-wide"
          type="submit"
          :disabled="submitting || (form.role === 'professional' && !serviceTypes.length)"
        >
          {{ submitting ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <p class="auth-switch">
        Already registered? <RouterLink to="/login">Sign in</RouterLink>
      </p>
    </section>
  </main>
</template>

