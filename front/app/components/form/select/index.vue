<template>
  <div class="form-select-wrap" :class="{ 'has-label': label }">
    <label v-if="label" :for="id" class="select-label">{{ label }}</label>
    <select
        :id="id"
        class="custom-select"
        :class="[size, { small: size === 'small' }]"
        :value="modelValue"
        :required="required"
        :disabled="disabled"
        @change="onChange"
    >
      <option v-if="placeholder" value="" :disabled="placeholderDisabled">{{ placeholder }}</option>
      <option
          v-for="opt in normalizedOptions"
          :key="String(opt.value)"
          :value="opt.value"
      >
        {{ opt.label }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Option = { value: string | number | boolean; label: string }
const selectRef = ref<HTMLSelectElement | null>(null)

const props = withDefaults(defineProps<{
  modelValue: string | number | boolean | null
  options: Option[] | string[]
  label?: string
  placeholder?: string
  placeholderDisabled?: boolean
  required?: boolean
  disabled?: boolean
  size?: 'default' | 'small'
  id?: string
}>(), {
  placeholderDisabled: false,
  required: false,
  disabled: false,
  size: 'default',
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number | boolean]
}>()

const normalizedOptions = computed<Option[]>(() =>
    props.options.map(o => (typeof o === 'string' ? { value: o, label: o } : o))
)

function onChange(e: Event) {
  const raw = (e.target as HTMLSelectElement).value
  // Coerce back to boolean if options use boolean values (e.g. is_active select)
  const match = normalizedOptions.value.find(o => String(o.value) === raw)
  emit('update:modelValue', match ? match.value : raw)
}


defineExpose({ focus: () => selectRef.value?.focus() })
</script>

<style scoped>
.form-select-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.select-label {
  font-size: 13px;
  color: var(--message-time-color);
}
.custom-select {
  box-sizing: border-box;
  width: 100%;
  height: 28px;
  padding: 0 8px;
  font-size: 12px;
  line-height: 26px;
  border-radius: var(--radius);
  background: var(--input-field-bg-color);
  color: var(--message-text-color);
  border: none;
  cursor: pointer;
  outline: none;
  transition: box-shadow 0.2s;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.custom-select:focus {
  border-color: var(--accent);
}
.custom-select.small {
  padding: 6px 8px;
  font-size: 13px;
}
.custom-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>