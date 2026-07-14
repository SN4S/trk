<template>
  <div class="listBlock" :class="{ alternating }">
    <div class="headerBlock">
      <slot name="header" />
    </div>
    <div :class="['bodyBlock beauty_table_scroll']" :style="heightStyle">
      <div v-show="loading" class="loading-overlay" aria-busy="true">
        <ui-loader :text="loadingText" />
      </div>
      <template v-if="empty && !loading">
        <div class="state-message empty">{{ emptyText }}</div>
      </template>
      <template v-else>
        <slot name="body" />
      </template>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  alternating: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  empty: {
    type: Boolean,
    default: false,
  },
  loadingText: {
    type: String,
    default: 'Завантаження...',
  },
  emptyText: {
    type: String,
    default: 'Дані не знайдено',
  },
  maxHeight: {
    type: Number,
    default: null,
  },
})

const heightStyle = computed(() => {
  if (props.maxHeight) {
    return { maxHeight: `${props.maxHeight}px`, overflow: 'auto' }
  }
  return null
})

provide('listAlternating', props.alternating)
</script>

<style scoped>
.listBlock {
  width: 100%;
  border: var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.headerBlock {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(50px, 1fr));
  gap: 1rem;
  min-height: 50px;
  background-color: var(--nav-bar-bg);
  padding: 0 1rem;
}

.bodyBlock {
  position: relative;
  border-bottom-left-radius: var(--radius);
  border-bottom-right-radius: var(--radius);
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;
}
</style>
