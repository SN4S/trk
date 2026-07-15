import { ref } from 'vue'

export interface ToastOptions {
  id?: string
  title: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error' | 'mention'
  duration?: number
  onClick?: () => void
}

const toasts = ref<ToastOptions[]>([])

export function useToast() {
  function addToast(options: ToastOptions) {
    const id = options.id || Math.random().toString(36).substring(2, 9)
    const duration = options.duration ?? 5000
    
    const toast = { ...options, id, type: options.type || 'info' }
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
  }

  function removeToast(id: string) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  return {
    toasts,
    addToast,
    removeToast
  }
}
