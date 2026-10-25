<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  booking: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['submit', 'skip'])
const selectedRating = ref(0)
const hoveredRating = ref(0)
const ratingLabels = ['', 'Needs improvement', 'Fair', 'Good', 'Very good', 'Excellent']

watch(() => props.open, (open) => {
  if (open) {
    selectedRating.value = 0
    hoveredRating.value = 0
  }
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open && booking" class="completion-rating-backdrop">
      <section class="completion-rating-modal" role="dialog" aria-modal="true" aria-labelledby="completion-rating-title">
        <div class="completion-rating-badge" aria-hidden="true"><span>✓</span></div>
        <p class="completion-rating-eyebrow">SERVICE COMPLETE · #{{ String(booking.booking_id).padStart(4, '0') }}</p>
        <h2 id="completion-rating-title">How did {{ booking.professional }} do?</h2>
        <p class="completion-rating-copy">Your {{ booking.service }} service is complete. A quick rating helps recognise great work.</p>
        <div class="completion-stars" role="radiogroup" aria-label="Rate this completed service" @mouseleave="hoveredRating = 0">
          <button
            v-for="star in 5"
            :key="star"
            type="button"
            role="radio"
            :aria-checked="selectedRating === star"
            :aria-label="`${star} star${star === 1 ? '' : 's'}`"
            :class="{ 'is-active': star <= (hoveredRating || selectedRating) }"
            @mouseenter="hoveredRating = star"
            @focus="hoveredRating = star"
            @blur="hoveredRating = 0"
            @click="selectedRating = star"
          >★</button>
        </div>
        <strong class="completion-rating-label">{{ ratingLabels[hoveredRating || selectedRating] || 'Choose from 1 to 5 stars' }}</strong>
        <p v-if="error" class="completion-rating-error">{{ error }}</p>
        <button class="completion-rating-submit" type="button" :disabled="!selectedRating || busy" @click="emit('submit', selectedRating)">{{ busy ? 'Sending rating…' : selectedRating ? `Submit ${selectedRating}-star rating` : 'Select a rating' }}</button>
        <button class="completion-rating-skip" type="button" :disabled="busy" @click="emit('skip')">Skip</button>
        <small>You can still add a rating and written review later from My bookings.</small>
      </section>
    </div>
  </Teleport>
</template>
