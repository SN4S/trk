export interface TicketStats {
    group_id: number | null
    all: number
    open: number
    pending: number
    closed: number
}

export function useTicketStats(groupId: MaybeRefOrGetter<number | null>) {
    const { apiFetch } = useApi()

    const stats = ref<TicketStats | null>(null)
    const pending = ref(false)
    const error = ref<string | null>(null)

    async function fetchStats() {
        pending.value = true
        error.value = null

        const gid = toValue(groupId)
        const params: Record<string, number> = {}
        if (gid !== null && gid !== undefined) params.group_id = gid

        try {
            stats.value = await apiFetch<TicketStats>('/stats', { params })
        } catch (e: any) {
            error.value = e?.data?.detail ?? 'Failed to load stats'
        } finally {
            pending.value = false
        }
    }

    watch(() => toValue(groupId), fetchStats, { immediate: true })

    return { stats, pending, error, refresh: fetchStats }
}