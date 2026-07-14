<template>
  <button type="button" class="reset-btn" @click="$emit('click')">
    <slot>Reset</slot>
  </button>
</template>

<script setup lang="ts">
defineEmits<{
  click: []
}>()
</script>

<style scoped>
.reset-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  opacity: 0.6;
  transition: opacity 0.2s, color 0.2s;
}
.reset-btn:hover {
  opacity: 1;
  color: #e05252;
}
</style>