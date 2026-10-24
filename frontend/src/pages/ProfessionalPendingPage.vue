<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const profile = ref(null)
const errorMessage = ref('')

async function checkApplication() {
  errorMessage.value = ''
  try {
    const response = await fetch('/api/professional/dashboard', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not check your application')

    if (data.approval_status === 'approved') {
      await router.replace('/professional/dashboard')
      return
    }
    if (data.approval_status === 'blocked') {
      await router.replace('/professional/blocked')
      return
    }
    profile.value = data
  } catch (error) {
    errorMessage.value = error.message
  }
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(checkApplication)
</script>

<template>
  <div class="review-page">
    <header class="review-header">
      <RouterLink class="workbench-logo" to="/">
        <span>HS</span><div><strong>HomeServe</strong><small>Professional application</small></div>
      </RouterLink>
      <button type="button" @click="logout">Sign out</button>
    </header>

    <main class="review-content">
      <section class="review-hero">
        <div class="review-orbit" aria-hidden="true"><span></span><b>01</b></div>
        <div>
          <p class="workbench-label">APPLICATION RECEIVED</p>
          <h1>We’re checking<br />the details, {{ user.username }}.</h1>
          <p>Your account is safe. You can explore how HomeServe works while the admin reviews your professional profile.</p>
          <button type="button" @click="checkApplication">Check status again</button>
          <small v-if="errorMessage" class="review-error">{{ errorMessage }}</small>
        </div>
      </section>

      <section class="review-progress" aria-label="Application progress">
        <article class="is-done"><span>01</span><div><strong>Application sent</strong><small>Your information reached HomeServe.</small></div></article>
        <article class="is-current"><span>02</span><div><strong>Admin verification</strong><small>Service and profile details are being checked.</small></div></article>
        <article><span>03</span><div><strong>Start receiving work</strong><small>Your field desk opens after approval.</small></div></article>
      </section>

      <section class="waiting-guide">
        <div class="waiting-guide__intro">
          <p class="workbench-label">WHILE YOU WAIT</p>
          <h2>Know the road ahead.</h2>
          <p>No need to keep refreshing. Sign in later and HomeServe will always take you to your latest application status.</p>
        </div>
        <div class="waiting-lessons">
          <article><span>A</span><h3>Jobs arrive clearly</h3><p>Each assignment includes its service type, address, schedule and current status.</p></article>
          <article><span>B</span><h3>You stay in control</h3><p>Review the request details before starting work and keep customers updated.</p></article>
          <article><span>C</span><h3>Good work builds trust</h3><p>Complete jobs carefully, communicate clearly and earn strong customer reviews.</p></article>
        </div>
      </section>

      <section v-if="profile" class="application-receipt">
        <div><p class="workbench-label">YOUR APPLICATION</p><h2>{{ profile.service }}</h2></div>
        <dl>
          <div><dt>Base city</dt><dd>{{ profile.city }}</dd></div>
          <div><dt>Experience</dt><dd>{{ profile.experience_years ?? 'Not provided' }}<span v-if="profile.experience_years"> years</span></dd></div>
          <div><dt>Current status</dt><dd>Pending review</dd></div>
        </dl>
      </section>
    </main>
  </div>
</template>
