<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  variant: { type: String, default: 'role' },
})
</script>

<template>
  <header :class="[variant === 'admin' ? 'section-page-heading' : 'role-section-heading', 'page-heading']">
    <div>
      <p v-if="eyebrow" class="workbench-label">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
    </div>
    <p v-if="description">{{ description }}</p>
  </header>
</template>
