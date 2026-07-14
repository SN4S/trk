<template>
  <div class="dashboardBlock">
    <span class="title">{{ title }}</span>
    <span class="data" :style="`color: ${color}`">{{ data }}</span>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  data: String,
  color: {
    type: String,
    default: '#000',
  },
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
