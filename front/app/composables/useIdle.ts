import { ref } from 'vue'

const isIdle = ref(false)
let idleTimer: ReturnType<typeof setTimeout> | undefined;
let throttleTimer: number | null = null;
const IDLE_TIMEOUT = 5000 // 15 seconds

function resetIdle() {
    isIdle.value = false
    clearTimeout(idleTimer)
    idleTimer = setTimeout(() => {
        isIdle.value = true
    }, IDLE_TIMEOUT)
}

function handleInteraction(e?: Event) {
    if (throttleTimer) return;
    
    throttleTimer = requestAnimationFrame(() => {
        if (e && e.type === 'mousemove') {
            const me = e as MouseEvent
            if (me.movementX === 0 && me.movementY === 0) {
                throttleTimer = null;
                return
            }
        }
        if (isIdle.value) {
            isIdle.value = false
            if (typeof window !== 'undefined') {
                window.dispatchEvent(new CustomEvent('user_active'))
            }
        }
        resetIdle()
        throttleTimer = null;
    })
}

let initialized = false

export function useIdle() {
    if (!initialized && typeof window !== 'undefined') {
        window.addEventListener('mousemove', handleInteraction, { passive: true })
        window.addEventListener('keydown', handleInteraction, { passive: true })
        window.addEventListener('mousedown', handleInteraction, { passive: true })
        window.addEventListener('wheel', handleInteraction, { passive: true })
        window.addEventListener('touchmove', handleInteraction, { passive: true })
        resetIdle()
        initialized = true
    }

    return {
        isIdle
    }
}
