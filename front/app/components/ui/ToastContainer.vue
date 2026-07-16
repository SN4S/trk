<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div 
        v-for="toast in toasts" 
        :key="toast.id" 
        class="toast" 
        :class="[`toast-${toast.type}`, { 'clickable': !!toast.onClick }]"
        @click="handleClick(toast)"
      >
        <div class="toast-icon">{{ getIcon(toast.type) }}</div>
        <div class="toast-content">
          <div class="toast-title">{{ toast.title }}</div>
          <div class="toast-message">{{ toast.message }}</div>
        </div>
        <button class="toast-close" @click.stop="removeToast(toast.id!)">×</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '~/composables/useToast'
import type { ToastOptions } from '~/composables/useToast'

const { toasts, removeToast } = useToast()

function getIcon(type?: string) {
  switch (type) {
    case 'mention': return '🔔'
    case 'success': return '✅'
    case 'warning': return '⚠️'
    case 'error': return '❌'
    default: return '💬'
  }
}

function handleClick(toast: ToastOptions) {
  if (toast.onClick) {
    toast.onClick()
    removeToast(toast.id!)
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column-reverse;
  gap: 10px;
  z-index: 9999;
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: var(--nav-bar-bg, #2c2c2e);
  color: var(--message-text-color, #fff);
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  width: 300px;
  border-left: 4px solid var(--accent, #168acd);
  transition: all 0.3s ease;
}

.toast.clickable {
  cursor: pointer;
}
.toast.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.4);
}

.toast-mention { border-left-color: #ff9800; }
.toast-success { border-left-color: #4caf50; }
.toast-warning { border-left-color: #ffc107; }
.toast-error { border-left-color: #f44336; }

.toast-icon {
  font-size: 20px;
  line-height: 1;
}

.toast-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toast-title {
  font-weight: 600;
  font-size: 14px;
}

.toast-message {
  font-size: 13px;
  opacity: 0.9;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.5;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 0;
}
.toast-close:hover {
  opacity: 1;
}

/* Animations */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.toast-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
