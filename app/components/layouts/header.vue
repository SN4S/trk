<template>
  <div class="header">
    <div class="dashboard_block">
      <header-dashboard
          v-for="stat in stats"
          :key="stat.title"
          :stat="stat">
      </header-dashboard>
    </div>
  </div>
</template>

<style scoped>
.header {
  height: 60px;
  border-bottom: 1px solid var(--border-color, #ccc);
  background-color: var(--message-bg-color);
}

.dashboard_block {
  display: flex;
  gap: 20px;
  height: 100%;
  align-items: stretch;
}
</style>

<script setup lang="ts">

const stats = [
  { title: 'Total Tickets', value: 128 },
  { title: 'Open', value: 34 },
  { title: 'Closed', value: 94 },
  { title: 'Overdue', value: 5 },
]
</script>