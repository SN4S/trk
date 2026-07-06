<template>
  <div class="wrapper_page">
    <div class="sidebar_block">
      <LayoutsSidebar />
    </div>
    <!-- Start Body -->
    <div class="body_block">
      <!-- Start Header -->
      <div class="header_block">
        <LayoutsHeader />
      </div>
      <!-- / Header -->
      <slot />
    </div>
    <!-- / Body -->
  </div>
</template>

<script setup></script>

<style scoped>
.wrapper_page {
  display: flex;
}

.sidebar_block {
  height: 100vh;
  width: 20%;
  border-right: 1px solid var(--border-color);
}

.body_block {
  height: 100vh;
  width: 80%;
}
</style>
