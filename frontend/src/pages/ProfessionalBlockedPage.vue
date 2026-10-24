<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')
const reason = ref(user.block_reason || '')
const loading = ref(true)

async function loadStatus() {
  try {
    const response = await fetch('/api/professional/dashboard', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) return

    if (data.approval_status === 'approved') {
      await router.replace('/professional/dashboard')
      return
    }
    if (data.approval_status === 'pending') {
      await router.replace('/professional/pending')
      return
    }
    reason.value = data.block_reason || 'The application did not meet the current verification requirements.'
  } finally {
    loading.value = false
  }
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(loadStatus)
</script>

<template>
  <div class="blocked-page">
    <header class="review-header blocked-header">
      <RouterLink class="workbench-logo" to="/">
        <span>HS</span><div><strong>HomeServe</strong><small>Application decision</small></div>
      </RouterLink>
      <button type="button" @click="logout">Sign out</button>
    </header>

    <main class="blocked-content">
      <section class="blocked-message">
        <div class="blocked-code">APPLICATION / 403</div>
        <p class="workbench-label">ACCOUNT ACCESS PAUSED</p>
        <h1>Your professional application cannot move forward right now.</h1>
        <p>Hi {{ user.username }}, the admin reviewed your application and left the following reason:</p>
      </section>

      <section class="decision-note">
        <span>ADMIN NOTE</span>
        <blockquote>{{ loading ? 'Loading the decision…' : reason }}</blockquote>
      </section>

      <section class="blocked-next-steps">
        <div><p class="workbench-label">WHAT NOW?</p><h2>This does not affect your data.</h2></div>
        <ol>
          <li><span>01</span><p>Read the admin note carefully and identify the missing or incorrect information.</p></li>
          <li><span>02</span><p>Keep your service documents and profile information ready for correction.</p></li>
          <li><span>03</span><p>Profile editing and re-submission will be added in the next project milestone.</p></li>
        </ol>
      </section>

      <button class="blocked-signout" type="button" @click="logout">Return to sign in</button>
    </main>
  </div>
</template>
