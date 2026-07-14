<template>
  <dialog
      ref="dialogRef"
      class="base-popup"
      :class="popupClass"
      @close="onNativeClose"
      @click="onBackdropClick"
      @cancel="onCancel"
  >
    <div class="popup-content" @click.stop>
      <header v-if="$slots.header || title" class="popup-header">
        <slot name="header">
          <h2>{{ title }}</h2>
        </slot>
        <button v-if="closable" class="popup-close" @click="close">✕</button>
      </header>

      <div class="popup-body">
        <slot />
      </div>

      <footer v-if="$slots.footer" class="popup-footer">
        <slot name="footer" :close="close" />
      </footer>
    </div>
  </dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  closable?: boolean
  closeOnOutsideClick?: boolean
  closeOnEsc?: boolean
  popupClass?: string
}>(), {
  closable: true,
  closeOnOutsideClick: true,
  closeOnEsc: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  opened: []
  closed: []
}>()

const dialogRef = ref<HTMLDialogElement | null>(null)

watch(() => props.modelValue, async (val) => {
  const el = dialogRef.value
  if (!el) return
  if (val && !el.open) {
    el.showModal()
    await nextTick()
    emit('opened')
  } else if (!val && el.open) {
    el.close()
  }
}, { immediate: true })

function close() {
  emit('update:modelValue', false)
}

function onNativeClose() {
  // fires for ESC and programmatic close()
  if (props.modelValue) emit('update:modelValue', false)
  emit('closed')
}

function onCancel(e: Event) {
  if (!props.closeOnEsc) e.preventDefault()
}

function onBackdropClick(e: MouseEvent) {
  if (props.closeOnOutsideClick && e.target === dialogRef.value) {
    close()
  }
}

defineExpose({ close })
</script>

<style scoped>
.base-popup {
  border: none;
  border-radius: var(--radius);
  background: var(--nav-bar-bg);
  color: var(--message-text-color);
  padding: 0;
}
.base-popup::backdrop {
  background: rgba(0, 0, 0, 0.5);
}

.popup-content {
  display: flex;
  flex-direction: column;
  min-width: 260px;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem 0;
}
.popup-header h2 {
  margin: 0;
  font-size: 15px;
}
.popup-close {
  background: none;
  border: none;
  color: var(--message-time-color);
  cursor: pointer;
  font-size: 13px;
  padding: 2px 4px;
}
.popup-close:hover { color: var(--accent); }

.popup-body {
  padding:1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.popup-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0 1.25rem 1.25rem;
}
</style>