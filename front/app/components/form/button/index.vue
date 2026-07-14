<template>
  <button 
    class="btn" 
    :type="type" 
    :disabled="disabled"
    @click="$emit('click')"
  >
    <template v-if="title">{{ title }}</template>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
defineProps({
  title: String,
  type: { type: String as () => 'button' | 'submit' | 'reset', default: 'button' },
  disabled: Boolean,
})
defineEmits(['click'])
</script>

<style scoped>
.btn {
  margin-top: 0.5rem;
  padding: 10px;
  border-radius: 8px;
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}
.btn:hover:not(:disabled) {
  opacity: 0.88;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>