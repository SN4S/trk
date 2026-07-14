<template>
  <span class="ticket_status" :class="status">{{ status }}</span>
</template>

<script setup lang="ts">
defineProps({
  status: String,
})
</script>

<style scoped>
.ticket_status {
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 10px;
  text-transform: uppercase;
  font-weight: bold;
  border-radius: 4px;
  padding: 1px 5px;
}

.ticket_status.open {
  background: rgba(224, 82, 82, 0.15);
  color: #e05252;
}

.ticket_status.pending {
  background: rgba(240, 173, 78, 0.15);
  color: #f0ad4e;
}

.ticket_status.closed {
  background: rgba(158, 192, 135, 0.15);
  color: #9ec087;
}
</style>