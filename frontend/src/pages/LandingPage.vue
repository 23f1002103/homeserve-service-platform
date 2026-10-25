<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import heroImage from '../assets/homeserve-hero.webp'

const landingData = ref(null)
const loading = ref(true)
const errorMessage = ref('')

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const dashboardPath = computed(() => {
  if (currentUser.role === 'admin') return '/admin/dashboard'
  if (currentUser.role === 'professional') return '/professional/dashboard'
  if (currentUser.role === 'customer') return '/customer/dashboard'
  return '/login'
})
const accountLabel = computed(() => currentUser.role ? 'Open dashboard' : 'Sign in')

function servicePath(service) {
  return currentUser.role === 'customer' ? `/customer/book/${service.id}` : dashboardPath.value
}

function money(value) {
  if (!value) return 'Price being prepared'
  return `From ${new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value))}`
}

async function loadLandingPage() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch('/api/landing')
    if (!response.ok) throw new Error(`The API returned HTTP ${response.status}`)
    landingData.value = await response.json()
  } catch (error) {
    errorMessage.value = 'We could not load the page. Make sure the Flask server is running.'
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(loadLandingPage)
</script>

<template>
  <div class="site-shell">
    <header class="site-header">
      <a class="brand" href="#top" aria-label="HomeServe home">
        <span class="brand-mark" aria-hidden="true">H</span><span>HomeServe</span>
      </a>
      <nav class="main-nav" aria-label="Main navigation">
        <a href="#services">Services</a><a href="#why-us">Why us</a>
      </nav>
      <RouterLink class="button button--small" :to="dashboardPath">{{ accountLabel }}</RouterLink>
    </header>

    <main id="top">
      <section v-if="loading" class="page-state" aria-live="polite">
        <span class="loader" aria-hidden="true"></span><p>Preparing your HomeServe experience…</p>
      </section>
      <section v-else-if="errorMessage" class="page-state page-state--error" role="alert">
        <p>{{ errorMessage }}</p><button class="button" type="button" @click="loadLandingPage">Try again</button>
      </section>

      <template v-else-if="landingData">
        <section class="hero-section" aria-labelledby="hero-title">
          <div class="hero-copy">
            <p class="eyebrow">{{ landingData.hero.eyebrow }}</p>
            <h1 id="hero-title">{{ landingData.hero.title }}</h1>
            <p class="hero-description">{{ landingData.hero.description }}</p>
            <div class="hero-actions">
              <a class="button" href="#services">Explore services</a>
              <a class="text-link" href="#why-us">See how it works <span>→</span></a>
            </div>
          </div>
          <div class="hero-visual">
            <img :src="heroImage" alt="A HomeServe professional arriving at a customer's home" />
            <div class="floating-note floating-note--top"><span class="note-icon">✓</span>Professional verified</div>
            <div class="floating-note floating-note--bottom"><span class="note-icon">⌂</span>Local help, clearly booked</div>
          </div>
        </section>

        <section id="services" class="section services-section" aria-labelledby="services-title">
          <div class="section-heading">
            <div><p class="eyebrow">Popular services</p><h2 id="services-title">Help for every corner of your home</h2></div>
            <p>Choose a service and connect with skilled professionals near you.</p>
          </div>
          <div v-if="landingData.services.length" class="service-grid">
            <article v-for="(service, index) in landingData.services" :key="service.id" class="service-card">
              <span class="service-number" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
              <div><h3>{{ service.name }}</h3><p>{{ service.description || 'Professional household help available through HomeServe.' }}</p></div>
              <footer><strong>{{ money(service.price) }}</strong><RouterLink class="card-link" :to="servicePath(service)">{{ currentUser.role === 'customer' ? 'Book service' : 'Get started' }} <span>→</span></RouterLink></footer>
            </article>
          </div>
          <div v-else class="services-empty"><span>Service catalogue</span><h3>New services are being prepared.</h3><p>The administrator has not published any bookable service yet.</p></div>
        </section>

        <section id="why-us" class="section trust-section" aria-labelledby="trust-title">
          <div class="trust-intro">
            <p class="eyebrow eyebrow--light">Why HomeServe</p>
            <h2 id="trust-title">Care, without<br />the guesswork.</h2>
            <p>From the first click to the completed job, every step tells you what happens next.</p>
            <span class="trust-signature"><b>HS</b> Household help, clearly booked.</span>
          </div>
          <ol class="service-journey">
            <li v-for="(highlight, index) in landingData.highlights" :key="highlight.value">
              <span class="journey-marker" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <small>{{ highlight.value }}</small>
                <h3>{{ highlight.label }}</h3>
                <p>{{ highlight.description }}</p>
              </div>
            </li>
          </ol>
        </section>
      </template>
    </main>

    <footer class="site-footer"><span>© 2026 HomeServe</span><span>Care for homes. Respect for your time.</span></footer>
  </div>
</template>
