export interface MentionableUser { id: number; username: string }

const users = ref<MentionableUser[]>([])
let fetched = false

export function useMentionableUsers() {
    const { apiFetch } = useApi()

    async function fetchUsers() {
        if (fetched) return
        fetched = true
        try {
            users.value = await apiFetch<MentionableUser[]>('/auth/users/mentionable')
        } catch (e) {
            console.error(e)
        }
    }

    onMounted(fetchUsers)
    return { users }
}