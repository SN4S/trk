<template>
  <div class="stat-card" v-if="stat">
    <div class="stat-title">{{ stat.title }}</div>
    <div class="stat-value">{{ stat.value }}</div>
  </div>
</template>

<script setup lang="ts">
interface StatItem {
  title: string
  value: number
}


defineProps<{
  stat?: StatItem
}>()
</script>

<style scoped>
.stat-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 10px 20px;
  background-color: var(--nav-bar-bg);
  border: 1px solid var(--border-color);
  min-width: 120px;
}

.stat-card:last-child {
  border-right: none;
}

.stat-title {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.default-card {
  background-color: #f9f9f9;
}
</style>