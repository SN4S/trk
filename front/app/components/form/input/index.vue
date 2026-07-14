<template>
  <div class="inputContainer">
    <label v-if="label" :for="id">{{ label }}</label>
    <input
        :id="id"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :disabled="disabled"
        :required="required"
        v-model="model"
    />
  </div>
</template>

<script setup lang="ts">
const model = defineModel<string>()

defineProps({
  id: String,
  label: String,
  type: { type: String, default: 'text' },
  placeholder: String,
  autocomplete: String,
  disabled: Boolean,
  required: Boolean,
})
</script>

<style scoped>
.inputContainer {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.inputContainer label {
  font-size: 13px;
  font-weight: 500;
  color: var(--message-time-color);
}
.inputContainer input {
  background: var(--input-field-bg-color);
  color: var(--message-text-color);
  border: none;
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 14px;
  outline: none;
  transition: box-shadow 0.2s;
}
.inputContainer input:focus {
  box-shadow: 0 0 0 2px var(--accent);
}
.inputContainer input:disabled {
  opacity: 0.6;
}
</style>