<script setup lang="ts">

</script>

<template>
  <div class="sidebar-logo">
    <NuxtLink to="/">
      <img src="@/assets/img/logo.svg" alt="Logo" />
    </NuxtLink>
  </div>
</template>

<style scoped>
.sidebar-logo {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}
.sidebar-logo a {
  display: flex;
  justify-content: center;
}
.sidebar-logo img {
  height: 28px;
}
</style>