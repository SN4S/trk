<template>
  <div class="dashboardBlock" :class="{ active }">
    <span class="title">{{ title }}</span>
    <span class="data" :style="`color: ${color}`">{{ data }}</span>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  data: [String, Number],
  color: {
    type: String,
    default: '#000',
  },
  active: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.dashboardBlock {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  border: var(--border);
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.dashboardBlock:hover {
  background: var(--nav-item-bg-hover-color);
}

.dashboardBlock.active {
  background: var(--nav-item-bg-hover-color);
  border-color: var(--accent);
}

.title {
  font-weight: 300;
  font-size: 12px;
}

.data {
  font-weight: 500;
  font-size: 20px;
}
</style>
