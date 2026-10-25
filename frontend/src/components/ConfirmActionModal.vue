<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  eyebrow: { type: String, default: 'Please confirm' },
  title: { type: String, required: true },
  description: { type: String, required: true },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Go back' },
  reasonLabel: { type: String, default: '' },
  reasonPlaceholder: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  danger: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])
const reason = ref('')

watch(() => props.open, (isOpen) => {
  if (isOpen) reason.value = ''
})

function confirm() {
  if (props.reasonLabel && !reason.value.trim()) return
  emit('confirm', reason.value.trim())
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="confirm-action-backdrop">
      <section class="confirm-action" role="dialog" aria-modal="true" :aria-label="title">
        <span class="confirm-action__mark" :class="{ 'is-danger': danger }" aria-hidden="true">{{ danger ? '!' : '✓' }}</span>
        <p>{{ eyebrow }}</p>
        <h2>{{ title }}</h2>
        <div class="confirm-action__description">{{ description }}</div>
        <label v-if="reasonLabel">
          {{ reasonLabel }}
          <textarea v-model.trim="reason" rows="3" maxlength="240" :placeholder="reasonPlaceholder" autofocus></textarea>
          <small>{{ reason.length }}/240</small>
        </label>
        <div class="confirm-action__buttons">
          <button type="button" class="confirm-action__cancel" :disabled="busy" @click="$emit('cancel')">{{ cancelLabel }}</button>
          <button type="button" class="confirm-action__confirm" :class="{ 'is-danger': danger }" :disabled="busy || (reasonLabel && !reason.trim())" @click="confirm">{{ busy ? 'Working…' : confirmLabel }}</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
