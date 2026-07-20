export function useChatScroll(key: Ref<string | number | null>) {
    const scrollPositions = useState<Record<string, number>>('chat:scroll', () => ({}))

    function save(el: HTMLElement | null) {
        if (!el || key.value == null) return
        scrollPositions.value[String(key.value)] = el.scrollTop
    }

    function restore(el: HTMLElement | null) {
        if (!el || key.value == null) return
        const saved = scrollPositions.value[String(key.value)]
        if (saved != null) {
            el.scrollTop = saved
            return true
        }
        return false
    }

    return { save, restore }
}