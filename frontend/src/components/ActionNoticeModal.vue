<script setup>
defineProps({
  open: { type: Boolean, default: false },
  eyebrow: { type: String, default: 'HomeServe update' },
  title: { type: String, required: true },
  description: { type: String, required: true },
  primaryLabel: { type: String, required: true },
  secondaryLabel: { type: String, default: 'Not now' },
  symbol: { type: String, default: 'HS' },
})

defineEmits(['primary', 'secondary'])
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="action-notice-backdrop" role="presentation">
      <section class="action-notice" role="dialog" aria-modal="true" :aria-label="title">
        <div class="action-notice__symbol" aria-hidden="true">{{ symbol }}</div>
        <p>{{ eyebrow }}</p>
        <h2>{{ title }}</h2>
        <span>{{ description }}</span>
        <div class="action-notice__actions">
          <button type="button" class="action-notice__primary" @click="$emit('primary')">{{ primaryLabel }}</button>
          <button type="button" class="action-notice__secondary" @click="$emit('secondary')">{{ secondaryLabel }}</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
