<script setup>
import { computed } from 'vue'
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

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const dashboardPath = computed(() => {
  if (currentUser.role === 'admin') return '/admin/dashboard'
  if (currentUser.role === 'professional') return '/professional/dashboard'
  if (currentUser.role === 'customer') return '/customer/dashboard'
  return '/login'
})
const accountLabel = computed(() => currentUser.role ? 'Open dashboard' : 'Sign in')
const servicesPath = computed(() => {
  if (currentUser.role === 'customer') return '/customer/services'
  if (currentUser.role) return dashboardPath.value
  return '/register'
})

// This is intentionally a fixed marketing catalogue. The authenticated
// customer catalogue remains controlled by the admin and service area.
const marketingServices = [
  { name: 'AC Service & Repair', description: 'Cooling care, routine servicing and dependable repair support.', image: acRepairImage },
  { name: 'Appliance Repair', description: 'Practical help for the everyday appliances your home relies on.', image: applianceImage },
  { name: 'Plumbing', description: 'Professional support for leaks, fittings and common water problems.', image: plumbingImage },
  { name: 'Carpentry', description: 'Skilled assistance for furniture, fixtures and household woodwork.', image: carpentryImage },
  { name: 'Home Cleaning', description: 'A fresher, more comfortable home without losing your whole day.', image: cleaningImage },
  { name: 'Electrical', description: 'Careful help with household electrical repairs and installations.', image: electricalImage },
]

const trustSteps = [
  { label: 'Simple', title: 'Book in a few steps', description: 'Choose the service, confirm the location and tell us what needs attention.', image: bookingImage },
  { label: 'Verified', title: 'Know who is arriving', description: 'Professionals are reviewed by the administrator before they can accept work.', image: verifiedImage },
  { label: 'Clear', title: 'Track every update', description: 'Follow the booking, payment and completion status from your HomeServe account.', image: paymentsImage },
]
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
      <section class="hero-section" aria-labelledby="hero-title">
        <div class="hero-copy">
          <p class="eyebrow">Trusted help for every home</p>
          <h1 id="hero-title">Your home deserves expert care.</h1>
          <p class="hero-description">Book verified professionals for repairs, cleaning and everyday home maintenance—without the usual hassle.</p>
          <div class="hero-actions">
            <RouterLink class="button" :to="servicesPath">Explore services</RouterLink>
            <a class="text-link" href="#why-us">See how it works <span>→</span></a>
          </div>
          <ul class="hero-assurances" aria-label="HomeServe benefits">
            <li>✓ Verified professionals</li><li>◷ Clear service updates</li><li>☆ Trusted home care</li>
          </ul>
        </div>
        <div class="hero-visual">
          <img :src="heroImage" alt="A welcoming modern home surrounded by greenery" />
          <div class="hero-service-orbit" aria-hidden="true">
            <span class="orbit-service orbit-service--ac"><img :src="acRepairImage" alt="" />AC Repair</span>
            <span class="orbit-service orbit-service--appliance"><img :src="applianceImage" alt="" />Appliance Repair</span>
            <span class="orbit-service orbit-service--cleaning"><img :src="cleaningImage" alt="" />Cleaning</span>
            <span class="orbit-service orbit-service--plumbing"><img :src="plumbingImage" alt="" />Plumbing</span>
          </div>
        </div>
      </section>

      <section id="services" class="section services-section" aria-labelledby="services-title">
        <div class="section-heading">
          <div><p class="eyebrow">Popular home care</p><h2 id="services-title">Help for every corner of your home</h2></div>
          <div class="section-heading__support">
            <p>Explore the kinds of household help HomeServe brings together. Sign in to see the live services available in your city.</p>
            <RouterLink class="service-price-note" :to="servicesPath">View available services →</RouterLink>
          </div>
        </div>
        <div class="service-grid">
          <article v-for="(service, index) in marketingServices" :key="service.name" class="service-card service-card--illustrated">
            <div class="service-card__top">
              <span class="service-number" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
              <img class="service-illustration" :src="service.image" alt="" loading="lazy" />
            </div>
            <div class="service-card__copy"><h3>{{ service.name }}</h3><p>{{ service.description }}</p></div>
            <footer><RouterLink class="card-link" :to="servicesPath">Check availability <span>→</span></RouterLink></footer>
          </article>
        </div>
      </section>

      <section id="why-us" class="section trust-section" aria-labelledby="trust-title">
        <div class="trust-intro">
          <p class="eyebrow eyebrow--light">Why HomeServe</p>
          <h2 id="trust-title">Care, without<br />the guesswork.</h2>
          <p>From the first click to the completed job, every step tells you what happens next.</p>
          <span class="trust-signature"><b>HS</b> Household help, clearly booked.</span>
        </div>
        <ol class="service-journey">
          <li v-for="step in trustSteps" :key="step.label">
            <div class="journey-visual"><img :src="step.image" alt="" loading="lazy" /></div>
            <div><small>{{ step.label }}</small><h3>{{ step.title }}</h3><p>{{ step.description }}</p></div>
          </li>
        </ol>
      </section>
    </main>

    <footer class="site-footer"><span>© 2026 HomeServe</span><span>Care for homes. Respect for your time.</span></footer>
  </div>
</template>
