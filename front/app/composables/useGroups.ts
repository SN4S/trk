export interface ApiGroup {
    id: number
    name: string
    tg_group_id: number | null
    last_message?: string | null
    last_time?: Date | null
}

export function useGroups() {
    const { apiFetch } = useApi()
    const { filter } = useFilter()
    const { subscribe, unsubscribe } = useWebSocket()
    const groups = useState<ApiGroup[]>('groups:list', () => [])
    const pending = useState('groups:pending', () => false)
    const error = useState<string | null>('groups:error', () => null)

    async function fetchGroups() {
        pending.value = true
        error.value = null

        const params: Record<string, string> = {}

        try {
            groups.value = await apiFetch<ApiGroup[]>('/groups/', { params })
        } catch (e: any) {
            error.value = e?.data?.detail ?? 'Failed to load groups'
        } finally {
            pending.value = false
        }
    }

    function onNewTicket() {
        fetchGroups()
    }

    // Fetch once on mount, no longer watching filter.search
    onMounted(() => {
        fetchGroups()
        subscribe('new_ticket', onNewTicket)
    })

    onUnmounted(() => {
        unsubscribe('new_ticket', onNewTicket)
    })

    return { groups, pending, error, fetchGroups }
}