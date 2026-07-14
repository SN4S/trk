<template>
  <div class="chat_block">
  <div class="admin-page">
    <admin-user></admin-user>
  </div>
  </div>
</template>

<script setup lang="ts">

</script>

<style scoped>
.admin-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--nav-bar-bg);
  color: var(--message-text-color);
  overflow-y: auto;
}
</style>
