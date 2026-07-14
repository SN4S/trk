<template>
  <div class="searchbar">
  <input
      id="search"
      type="text"
      :placeholder="placeholder"
      :value="filter.search"
      @input="setSearch(($event.target as HTMLInputElement).value)"
  /></div>
</template>

<script setup lang="ts">
import { useFilter } from '~/composables/useFilter'

const { filter, isChatMode, setSearch } = useFilter()

const placeholder = computed(() =>
    isChatMode.value ? 'Пошук у чаті...' : 'Пошук...'
)
</script>


<style scoped>
  input{
    background-color: var(--input-field-bg-color);
    border-radius: 30px;
    padding-left: 1rem;
    border: none;
    width: 100%;
    line-height: 34px;
  }
  .searchbar{
    display: flex;
    width: 65%;
  }
</style>