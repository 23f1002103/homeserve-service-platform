<script setup>
defineProps({
  job: { type: Object, required: true },
  accepting: { type: Boolean, default: false },
  preview: { type: Boolean, default: false },
})

defineEmits(['accept'])

function scheduleParts(value) {
  if (!value) return { date: 'Date pending', time: 'Time pending' }
  const scheduled = new Date(value)
  return {
    date: scheduled.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
    time: scheduled.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' }),
  }
}
</script>

<template>
  <article class="available-job-card">
    <header class="available-job-card__header">
      <div><code>#{{ String(job.id).padStart(4, '0') }}</code><span class="job-type-badge" :class="`is-${job.booking_type}`">{{ job.booking_type === 'combo' ? 'Combo job' : 'Standard' }}</span></div>
      <p class="workbench-label">{{ job.service }}</p>
      <h2>{{ job.description }}</h2>
      <small v-if="job.booking_type === 'combo'">{{ job.package_name }} · Service {{ job.combo_position }} of {{ job.combo_total }}</small>
    </header>

    <section class="available-job-route" aria-label="Approximate route to the customer service area">
      <div class="route-preview" aria-hidden="true">
        <span class="route-point is-origin"></span>
        <svg viewBox="0 0 220 66" preserveAspectRatio="none"><path d="M12 48C54 3 118 65 208 18" /></svg>
        <span class="route-point is-destination"></span>
      </div>
      <div class="route-labels"><span>You</span><span>{{ job.area }}</span></div>
      <strong>{{ job.distance_km !== null ? `${job.distance_km} km away` : 'Within your work area' }}</strong>
      <small>Approximate area only · exact address unlocks after acceptance</small>
    </section>

    <footer class="available-job-card__meta">
      <div><small>SCHEDULE</small><strong>{{ scheduleParts(job.scheduled_for).date }}</strong><span>{{ scheduleParts(job.scheduled_for).time }}</span></div>
      <div><small>YOUR EARNING</small><strong>₹{{ job.professional_earning || job.price || '—' }}</strong><span v-if="job.price">Service price ₹{{ job.price }}</span></div>
      <RouterLink v-if="preview" to="/professional/jobs">View and accept</RouterLink>
      <button v-else type="button" :disabled="accepting" @click="$emit('accept', job)">{{ accepting ? 'Accepting…' : 'Accept job' }}</button>
    </footer>
  </article>
</template>
