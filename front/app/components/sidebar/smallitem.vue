<template>
  <NuxtLink :to="to" class="small-item-btn">
    <span v-if="icon" class="icon">{{ icon }}</span>
    <span class="title">{{ title }}</span>
  </NuxtLink>
</template>

<script setup lang="ts">
defineProps<{
  to: string
  icon?: string
  title: string
}>()
</script>

<style scoped>
.small-item-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  text-decoration: none;
  color: var(--message-text-color);
  font-weight: 500;
  border-bottom: 1px solid var(--border);
  transition: background 0.2s;
}
.small-item-btn:hover {
  background: var(--nav-item-bg-hover-color);
}
.small-item-btn.router-link-exact-active {
  background: var(--nav-item-bg-active-color);
}
.small-item-btn.router-link-exact-active .title,
.small-item-btn.router-link-exact-active .icon {
  color: var(--second-test-color);
}
.icon {
  font-size: 16px;
}
</style>
