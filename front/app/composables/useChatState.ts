const scrollPositions = new Map<string, number>()

export function useChatScroll(key: Ref<string | number | null>) {
    function save(el: HTMLElement | null) {
        if (!el || key.value == null) return
        scrollPositions.set(String(key.value), el.scrollTop)
    }

    function restore(el: HTMLElement | null) {
        if (!el || key.value == null) return
        const saved = scrollPositions.get(String(key.value))
        if (saved != null) {
            el.scrollTop = saved
            return true
        }
        return false
    }

    return { save, restore }
}