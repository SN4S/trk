<template>
  <div class="itemBox">
    <span
        v-if="String(text) && !image"
        ref="textElement"
        class="text"
    >
      {{ text }}
    </span>
    <slot />
  </div>
</template>

<script setup>
const props = defineProps({
  text: [String, Number],
  src: String,
  image: {
    type: Boolean,
    default: false,
  },
})


</script>

<style scoped>
.itemBox {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.text {
  text-align: center;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>

