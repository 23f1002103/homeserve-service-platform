<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import heroImage from '../assets/homesur-hero-3d.jpg'
import plumbingImage from '../assets/service-plumbing.png'
import electricalImage from '../assets/service-electrical.png'
import cleaningImage from '../assets/service-cleaning.png'
import applianceImage from '../assets/service-appliance.png'
import acRepairImage from '../assets/service-ac-repair.png'
import carpentryImage from '../assets/service-carpentry.png'
import bookingImage from '../assets/feature-booking.png'
import verifiedImage from '../assets/feature-verified.png'
import paymentsImage from '../assets/feature-payments.png'

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

const serviceImages = {
  plumbing: plumbingImage,
  electrical: electricalImage,
  cleaning: cleaningImage,
  'home cleaning': cleaningImage,
  'appliance repair': applianceImage,
  'ac service & repair': acRepairImage,
  'ac service and repair': acRepairImage,
  carpentry: carpentryImage,
}

const featureDetails = {
  Simple: { image: bookingImage, title: 'Easy booking' },
  Verified: { image: verifiedImage, title: 'Verified professionals' },
  Upfront: { image: paymentsImage, title: 'Secure payments' },
}

const featuredServices = computed(() => (
  landingData.value?.services.filter((service) => serviceImage(service)) || []
))

const startingPrice = computed(() => {
  const prices = featuredServices.value
    .map((service) => Number(service.price))
    .filter((price) => Number.isFinite(price) && price > 0)

  if (!prices.length) return ''
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Math.min(...prices))
})

function servicePath(service) {
  return currentUser.role === 'customer' ? `/customer/book/${service.id}` : dashboardPath.value
}

function serviceImage(service) {
  return serviceImages[service.name.trim().toLowerCase()] || null
}

function featureDetail(highlight) {
  return featureDetails[highlight.value] || null
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
            <img :src="heroImage" alt="A welcoming modern home surrounded by greenery" />
          </div>
        </section>

        <section id="services" class="section services-section" aria-labelledby="services-title">
          <div class="section-heading">
            <div><p class="eyebrow">Popular services</p><h2 id="services-title">Help for every corner of your home</h2></div>
            <div class="section-heading__support">
              <p>Choose a service and connect with skilled professionals near you.</p>
              <p v-if="startingPrice" class="service-price-note">Home care for every budget—services start at {{ startingPrice }}.</p>
            </div>
          </div>
          <div v-if="featuredServices.length" class="service-grid">
            <article v-for="(service, index) in featuredServices" :key="service.id" class="service-card service-card--illustrated">
              <div class="service-card__top">
                <span class="service-number" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
                <img v-if="serviceImage(service)" class="service-illustration" :src="serviceImage(service)" alt="" loading="lazy" />
              </div>
              <div class="service-card__copy"><h3>{{ service.name }}</h3><p>{{ service.description || 'Professional household help available through HomeServe.' }}</p></div>
              <footer><RouterLink class="card-link" :to="servicePath(service)">{{ currentUser.role === 'customer' ? 'Book service' : 'Get started' }} <span>→</span></RouterLink></footer>
            </article>
          </div>
          <div v-else class="services-empty"><span>Featured services</span><h3>New featured services are being prepared.</h3><p>Please check again soon for services available to book from the homepage.</p></div>
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
              <div class="journey-visual">
                <img v-if="featureDetail(highlight)" :src="featureDetail(highlight).image" alt="" loading="lazy" />
                <span v-else class="journey-marker" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
              </div>
              <div>
                <small>{{ highlight.value }}</small>
                <h3>{{ featureDetail(highlight)?.title || highlight.label }}</h3>
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
