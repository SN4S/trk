/**
 * Global filter state — shared between sidebar search, filter panel,
 * and the ticket list (both global and per-group views).
 *
 * Rules:
 *  - search is always active (global or per-group)
 *  - themeId / status filter applies globally or inside a group
 *  - activeGroupId is set by the router; when set, search/filter
 *    operates exclusively on that group's tickets
 */

export type TicketStatus = 'open' | 'pending' | 'closed'

export interface FilterState {
    search: string
    themeId: number | null
    status: TicketStatus | null
    assignedToMe: boolean
}

export function useFilter() {
    const state = useState<FilterState>('filter:state', () => ({
        search: '',
        themeId: null,
        status: null,
        assignedToMe: false,
    }))

    const route = useRoute()

    /** The currently open group ID (null = global / no chat open) */
    const activeGroupId = computed<number | null>(() => {
        const id = route.params.id
        if (!id) return null
        const parsed = parseInt(id as string, 10)
        return isNaN(parsed) ? null : parsed
    })

    const isGeneralMode = computed(() => route.path.startsWith('/general'))

    const isChatMode = computed(() => activeGroupId.value !== null || isGeneralMode.value)

    function setSearch(val: string) {
        state.value.search = val
    }

    function setTheme(id: number | null) {
        state.value.themeId = id
    }

    function setStatus(s: TicketStatus | null) {
        state.value.status = s
    }

    function setAssignedToMe(val: boolean) {
        state.value.assignedToMe = val
    }

    function reset() {
        state.value.search = ''
        state.value.themeId = null
        state.value.status = null
        state.value.assignedToMe = false
    }

    return {
        /** Reactive filter values */
        filter: readonly(state.value),
        activeGroupId,
        isChatMode,
        setSearch,
        setTheme,
        setStatus,
        setAssignedToMe,
        reset,
    }
}