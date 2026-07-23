export interface TicketStats {
    group_id: number | null
    all: number
    open: number
    pending: number
    closed: number
}

export function useTicketStats(groupId: MaybeRefOrGetter<number | null>) {
    const { apiFetch } = useApi()
    const { subscribe, unsubscribe } = useWebSocket()
    const stats = useState<TicketStats | null>(`ticket-stats:${toValue(groupId) ?? 'all'}`, () => null)
    const pending = useState(`ticket-stats:pending:${toValue(groupId) ?? 'all'}`, () => false)
    const error = useState<string | null>(`ticket-stats:error:${toValue(groupId) ?? 'all'}`, () => null)

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

    function onTicketEvent() {
        fetchStats()
    }

    onMounted(() => {
        subscribe('new_ticket', onTicketEvent)
        subscribe('update_ticket', onTicketEvent)
    })

    onUnmounted(() => {
        unsubscribe('new_ticket', onTicketEvent)
        unsubscribe('update_ticket', onTicketEvent)
    })

    return { stats, pending, error, refresh: fetchStats }
}