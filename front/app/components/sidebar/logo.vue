<script setup lang="ts">

</script>

<template>
  <!--START LOGO-->
  <div class="sidebar-logo">
    <NuxtLink to="/">
      <img src="@/assets/img/logo.svg" alt="Logo" />
    </NuxtLink>
  </div>
  <!--END LOGO-->
</template>

<style scoped>
.sidebar-logo {
  padding: 14px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.sidebar-logo img {
  height: 28px;
}
</style>