<template>
  <div class="listContainer" >
    <slot />
  </div>
</template>

<script setup lang="ts">

</script>

<style scoped>
.listContainer {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(50px, 1fr));
  grid-auto-flow: column;
  gap: 1rem;
  min-height: 70px;
  background-color: white;
  cursor: pointer;
  transition: 0.9s;
  padding: 0 1rem;
  border-top: var(--border);
}
</style>