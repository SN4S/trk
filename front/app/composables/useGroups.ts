export interface ApiGroup {
    id: number
    name: string
    tg_group_id: number | null
}

export function useGroups() {
    const { apiFetch } = useApi()
    const { filter } = useFilter()

    const groups = ref<ApiGroup[]>([])
    const pending = ref(false)
    const error = ref<string | null>(null)

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

    // Fetch once on mount, no longer watching filter.search
    onMounted(() => {
        fetchGroups()
    })

    return { groups, pending, error, fetchGroups }
}