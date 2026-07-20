import type {ApiTicket} from "~/composables/useTickets";

export interface ApiReply {
    id: number
    ticket_id: number
    message: string
    is_support: boolean
    user_id: number | null
    created_at: string
    tg_message_id: number | null
    reply_to_reply_id: number | null

    ticket: { id: number; name: string ;soc_user_name:string } | null
    user: { id: number; username: string } | null
    parent_reply: { id: number; message: string; user: { id: number; username: string } | null } | null
}


export function useRepliesT(ticketId?: MaybeRef<number | null>) {
    const { apiFetch } = useApi()
    const { filter } = useFilter()
    const { subscribe, unsubscribe } = useWebSocket()

    const replies = useState<ApiReply[]>(`replies-t:list:${toValue(ticketId) ?? 'all'}`, () => [])
    const pending = useState(`replies-t:pending:${toValue(ticketId) ?? 'all'}`, () => false)
    const error = useState<string | null>(`replies-t:error:${toValue(ticketId) ?? 'all'}`, () => null)

    async function fetchReplies() {
        pending.value = true
        error.value = null

        const tid = toValue(ticketId)

        // Build query params — only include non-null/non-empty values
        const params: Record<string, string | number> = {}

        if (tid !== null && tid !== undefined) params.ticket_id = tid
        if (filter.status) params.status = filter.status
        if (filter.themeId !== null) params.theme_id = filter.themeId
        if (filter.search.trim()) params.search = filter.search.trim()

        const { currentUser } = useAuth()
        if (filter.assignedToMe && currentUser.value) {
            const role = currentUser.value.role
            if (role === 'support') {
                params.assigned_to_id = currentUser.value.id
            } else if (role === 'admin' || role === 'manager') {
                params.assigned_by_id = currentUser.value.id
            }
        }

        try {
            replies.value = await apiFetch<ApiReply[]>('/tickets/'+ tid + '/replies/', { params })
        } catch (e: any) {
            error.value = e?.data?.detail ?? 'Failed to load relies'
        } finally {
            pending.value = false
        }
    }

    // Refetch when any filter value or the group changes
    watch(
        [() => toValue(ticketId), () => filter.search, () => filter.status, () => filter.themeId, () => filter.assignedToMe],
        () => fetchReplies(),
        { immediate: true },
    )

    function onNewReply(data: any) {
        // Only fetch if the reply belongs to this ticket
        if (data.ticket_id === toValue(ticketId)) {
            fetchReplies()
        }
    }

    onMounted(() => subscribe('new_reply', onNewReply))
    onUnmounted(() => unsubscribe('new_reply', onNewReply))

    return { replies, pending, error, fetchReplies }
}

export function useRepliesG(groupId?: MaybeRef<number | null>) {
    const { apiFetch } = useApi()
    const { filter } = useFilter()
    const { subscribe, unsubscribe } = useWebSocket()

    const replies = useState<ApiReply[]>(`replies-g:list:${toValue(groupId) ?? 'all'}`, () => [])
    const pending = useState(`replies-g:pending:${toValue(groupId) ?? 'all'}`, () => false)
    const error = useState<string | null>(`replies-g:error:${toValue(groupId) ?? 'all'}`, () => null)

    async function fetchReplies() {
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
                params.assigned_to_id = currentUser.value.id
            } else if (role === 'admin' || role === 'manager') {
                params.assigned_by_id = currentUser.value.id
            }
        }

        try {
            if (gid !== null && gid !== undefined) {
                replies.value = await apiFetch<ApiReply[]>('/groups/'+ gid + '/replies', { params })
            } else {
                replies.value = await apiFetch<ApiReply[]>('/replies', { params })
            }
        } catch (e: any) {
            error.value = e?.data?.detail ?? 'Failed to load replies'
        } finally {
            pending.value = false
        }
    }

    // Refetch when any filter value or the group changes
    watch(
        [() => toValue(groupId), () => filter.search, () => filter.status, () => filter.themeId, () => filter.assignedToMe],
        () => fetchReplies(),
        { immediate: true },
    )

    function onNewReply(data: any) {
        // Refetch regardless, let the backend filter by group
        fetchReplies()
    }

    onMounted(() => subscribe('new_reply', onNewReply))
    onUnmounted(() => unsubscribe('new_reply', onNewReply))

    return { replies, pending, error, fetchReplies }
}