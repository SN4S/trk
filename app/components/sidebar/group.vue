<template>
<div class="group">
<button class="group__header" @click="open = !open">
  <span>{{ title }}</span>
  <ChevronDown class="chevron" :class="{ 'chevron--open': open }" />
</button>

<ul v-show="open" class="group__items">
  <slot />
</ul>
</div>
</template>

<script setup lang="ts">

defineProps<{
  title: string
}>()

const open = ref(true)
</script>

<style scoped>
.group__header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
}
.group__header:hover {
  color: #fff;
}
.chevron {
  margin-left: auto;
  width: 14px;
  height: 14px;
  transition: transform 0.15s;
}
.chevron--open {
  transform: rotate(180deg);
}
.group__items {
  list-style: none;
  margin: 0;
  padding: 0;
}
.group__items :deep(li) {
  list-style: none;
}
.group__items :deep(a) {
  display: block;
  padding: 8px 16px 8px 32px;
  color: #d1d5db;
  text-decoration: none;
  font-size: 14px;
}
.group__items :deep(a:hover) {
  background: #1f2937;
  color: #fff;
}
.group__items :deep(a.router-link-active) {
  background: #2563eb;
  color: #fff;
}
</style>