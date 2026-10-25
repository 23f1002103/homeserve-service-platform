<script setup>
defineProps({
  page: { type: Number, required: true },
  pageCount: { type: Number, required: true },
  total: { type: Number, required: true },
  visibleCount: { type: Number, required: true },
  label: { type: String, default: 'records' },
})

defineEmits(['update:page'])
</script>

<template>
  <nav v-if="total" class="list-pagination" :aria-label="`${label} pages`">
    <span>Showing {{ visibleCount }} of {{ total }} {{ label }}</span>
    <div>
      <button type="button" :disabled="page === 1" @click="$emit('update:page', page - 1)">Previous</button>
      <code>{{ page }} / {{ pageCount }}</code>
      <button type="button" :disabled="page === pageCount" @click="$emit('update:page', page + 1)">Next</button>
    </div>
  </nav>
</template>
