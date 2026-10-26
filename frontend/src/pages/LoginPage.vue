<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import GoogleSignInButton from '../components/GoogleSignInButton.vue'

const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const submitting = ref(false)

async function finishAuthentication(data) {
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))
  sessionStorage.removeItem('professional_location_verified')

  if (data.user.role === 'admin') {
    await router.push('/admin/dashboard')
  } else if (data.user.role === 'customer') {
    await router.push('/customer/dashboard')
  } else if (data.user.role === 'professional') {
    if (data.user.approval_status === 'approved') {
      await router.push('/professional/location')
    } else if (data.user.approval_status === 'blocked') {
      await router.push('/professional/blocked')
    } else {
      await router.push('/professional/pending')
    }
  } else {
    await router.push('/')
  }
}

function showGoogleError(message) {
  errorMessage.value = message
}

async function login() {
  errorMessage.value = ''
  submitting.value = true

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Login failed')
    }

    await finishAuthentication(data)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <RouterLink class="auth-brand" to="/">HomeServe</RouterLink>

    <section class="auth-card" aria-labelledby="login-title">
      <p class="eyebrow">Welcome back</p>
      <h1 id="login-title">Sign in to your account</h1>
      <p v-if="route.query.registered" class="form-success">
        Registration successful. You can sign in now.
      </p>
      <p v-if="route.query.expired" class="form-error" role="alert">
        Your session expired. Please sign in again.
      </p>

      <GoogleSignInButton
        @authenticated="finishAuthentication"
        @error="showGoogleError"
      />

      <form @submit.prevent="login">
        <label>
          Email
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label>
          Password
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>

        <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
        <button class="button auth-submit" type="submit" :disabled="submitting">
          {{ submitting ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p class="auth-switch">
        New to HomeServe? <RouterLink to="/register">Create an account</RouterLink>
      </p>
    </section>
  </main>
</template>

