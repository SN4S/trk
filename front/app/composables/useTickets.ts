/**
 * Tickets composable — fetches tickets from the API with all filter params
 * (search, theme_id, status, group_id) sent server-side.
 *
 * Watches the shared filter state and refetches automatically whenever
 * any filter value changes. No client-side filtering is performed.
 */

import type { TicketStatus } from '~/composables/useFilter'

export interface ApiTicketAssignment {
    id: number
    ticket_id: number
    assigned_to: { id: number; username: string } | null
    assigned_by: { id: number; username: string }
    assigned_at: string
}

export interface ApiTicket {
    id: number
    ticket_num: string
    theme_id: number
    group_id: number
    soc_user_id: number
    soc_user_name: string
    message: string | null
    status: TicketStatus
    created_at: string
    updated_at: string | null
    theme: { id: number; name: string } | null
    group: { id: number; name: string } | null
    current_assignment: ApiTicketAssignment | null
}

export function useTickets(groupId?: MaybeRef<number | null>) {
    const { apiFetch } = useApi()
    const { filter } = useFilter()
    const { subscribe, unsubscribe } = useWebSocket()

    const tickets = ref<ApiTicket[]>([])
    const pending = ref(false)
    const error = ref<string | null>(null)

    async function fetchTickets() {
        pending.value = true
        error.value = null

        const gid = toValue(groupId)

        // Build query params — only include non-null/non-empty values
        const params: Record<string, string | number> = {}

        if (gid !== null && gid !== undefined) params.group_id = gid
        if (filter.status) params.status = filter.status
        if (filter.themeId !== null) params.theme_id = filter.themeId
        if (filter.search.trim()) params.search = filter.search.trim()
        
        const { currentUser } = useAuth()
        if (filter.assignedToMe && currentUser.value) {
            const role = currentUser.value.role
            if (role === 'support') {
                // Support: show tickets currently assigned TO me
                params.assigned_to_id = currentUser.value.id
            } else if (role === 'admin' || role === 'manager') {
                // Admin/Manager: show tickets I have assigned to someone
                params.assigned_by_id = currentUser.value.id
            }
        }

        try {
            tickets.value = await apiFetch<ApiTicket[]>('/tickets/', { params })
        } catch (e: any) {
            error.value = e?.data?.detail ?? 'Failed to load tickets'
        } finally {
            pending.value = false
        }
    }

    // Refetch when any filter value or the group changes
    watch(
        [() => toValue(groupId), () => filter.search, () => filter.status, () => filter.themeId, () => filter.assignedToMe],
        () => fetchTickets(),
        { immediate: true },
    )

    function onTicketEvent(data: any) {
        fetchTickets()
    }

    onMounted(() => {
        subscribe('new_ticket', onTicketEvent)
        subscribe('update_ticket', onTicketEvent)
    })

    onUnmounted(() => {
        unsubscribe('new_ticket', onTicketEvent)
        unsubscribe('update_ticket', onTicketEvent)
    })

    return { tickets, pending, error, fetchTickets }
}
