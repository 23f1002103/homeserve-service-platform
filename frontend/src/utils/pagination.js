import { computed, ref, watch } from 'vue'

export function usePagination(items, pageSize = 8) {
  const currentPage = ref(1)
  const pageCount = computed(() => Math.max(1, Math.ceil(items.value.length / pageSize)))
  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    return items.value.slice(start, start + pageSize)
  })

  watch(pageCount, (lastPage) => {
    if (currentPage.value > lastPage) currentPage.value = lastPage
  })

  function resetPage() {
    currentPage.value = 1
  }

  return { currentPage, pageCount, paginatedItems, resetPage }
}
