import { ref, onMounted, onUnmounted } from 'vue'
import { useApi } from '~/composables/useApi'
import { useWebSocket } from '~/composables/useWebSocket'
import { useAuth } from '~/composables/useAuth'
import { useToast } from '~/composables/useToast'
import { useRouter } from 'vue-router'

export interface ApiNotification {
    id: number
    user_id: number
    type: string
    data: any
    is_read: boolean
    created_at: string
}

export function useNotifications() {
    const { apiFetch } = useApi()
    const { subscribe, unsubscribe } = useWebSocket()
    const { isLoggedIn } = useAuth()
    const router = useRouter()
    const notifications = useState<ApiNotification[]>('notifications:list', () => [])
    const pending = useState('notifications:pending', () => false)
    const error = useState<string | null>('notifications:error', () => null)

    async function fetchNotifications() {
        if (!isLoggedIn.value) return
        pending.value = true
        error.value = null
        try {
            const data = await apiFetch<ApiNotification[]>('/notifications')
            notifications.value = data
        } catch (e: any) {
            error.value = e?.message || 'Помилка завантаження сповіщень'
        } finally {
            pending.value = false
        }
    }

    async function markAsRead(id: number) {
        try {
            await apiFetch(`/notifications/${id}/read`, { method: 'POST' })
            const n = notifications.value.find(n => n.id === id)
            if (n) n.is_read = true
        } catch (e: any) {
            console.error('Помилка при прочитанні сповіщення', e)
        }
    }

    function onNewNotification(payload: ApiNotification) {
        // Only append if it's actually unread
        if (!payload.is_read) {
            notifications.value.unshift(payload)

            let title = 'Сповіщення'
            let message = ''
            let hash = ''
            let routePath = '/'

            if (payload.type === 'new_ticket') {
                title = `Новий запит #${payload.data?.ticket_num || ''}`
                const author = payload.data?.soc_user_name || 'Клієнт'
                message = `Від ${author}: ${payload.data?.message || ''}`
                hash = `ticket-${payload.data?.id}`
            } else if (payload.type === 'status_change') {
                title = `Оновлено тікет #${payload.data?.ticket_num || ''}`
                const status = payload.data?.status || 'оновлено'
                message = `Статус змінено на: ${status}`
                hash = `ticket-${payload.data?.id}`
            } else if (payload.type === 'assign_ticket') {
                const assignedBy = payload.data?.current_assignment?.assigned_by?.username || 'Колега'
                title = `${assignedBy} призначив(ла) тікет #${payload.data?.ticket_num || ''}`
                const assignedTo = payload.data?.current_assignment?.assigned_to?.username || 'Вас'
                message = `Тікет було призначено на ${assignedTo}`
                hash = `ticket-${payload.data?.id}`
            } else if (payload.type === 'new_reply') {
                title = `Нова відповідь`
                const author = payload.data?.user?.username || payload.data?.soc_user_name || 'Клієнт'
                message = `${author}: ${payload.data?.message || ''}`
                hash = `reply-${payload.data?.id}`
            } else if (payload.type === 'new_general_message') {
                title = `Загальний чат`
                const author = payload.data?.user?.username || 'Колега'
                message = `${author}: ${payload.data?.message || ''}`
                hash = `reply-${payload.data?.id}` // General chat uses reply-id too!
                routePath = '/general'
            }

            const { addToast } = useToast()
            addToast({
                title,
                message,
                type: 'info',
                onClick: async () => {
                    const el = document.getElementById(hash)
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        el.classList.add('highlight-ticket')
                        setTimeout(() => el.classList.remove('highlight-ticket'), 2000)
                    } else {
                        await router.push(`${routePath === '/' ? '' : routePath}/#${hash}`)
                    }
                }
            })
        }
    }

    // Optional helper to mount lifecycle handlers easily
    function initNotifications() {
        onMounted(() => {
            fetchNotifications()
            subscribe('notification', onNewNotification)
        })
        onUnmounted(() => {
            unsubscribe('notification', onNewNotification)
        })
    }

    return {
        notifications,
        pending,
        error,
        fetchNotifications,
        markAsRead,
        initNotifications
    }
}
