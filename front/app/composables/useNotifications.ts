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
    
    const notifications = ref<ApiNotification[]>([])
    const pending = ref(false)
    const error = ref<string | null>(null)

    async function fetchNotifications() {
        if (!isLoggedIn.value) return
        pending.value = true
        error.value = null
        try {
            const data = await apiFetch<ApiNotification[]>('/notifications?unread_only=true')
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
            notifications.value = notifications.value.filter(n => n.id !== id)
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
                title = 'Новий тікет'
                message = `Створено тікет #${payload.data?.ticket_num || ''}`
                hash = `ticket-${payload.data?.id}`
            } else if (payload.type === 'update_ticket' || payload.type === 'assign_ticket') {
                title = 'Оновлення тікета'
                message = `Тікет #${payload.data?.ticket_num || ''} оновлено/призначено`
                hash = `ticket-${payload.data?.id}`
            } else if (payload.type === 'new_reply') {
                title = 'Нова відповідь'
                const author = payload.data?.user?.username || payload.data?.soc_user_name || 'Клієнт'
                message = `${author}: ${payload.data?.message || ''}`
                hash = `ticket-${payload.data?.ticket_id}`
            } else if (payload.type === 'new_general_message') {
                title = 'Загальний чат'
                const author = payload.data?.user?.username || 'Колега'
                message = `${author}: ${payload.data?.message || ''}`
                hash = `msg-${payload.data?.id}`
                routePath = '/general'
            }

            const { addToast } = useToast()
            addToast({
                title,
                message,
                type: 'info',
                onClick: async () => {
                    const router = useRouter()
                    if (routePath === '/general') {
                        await router.push(`/general#${hash}`)
                    } else {
                        if (router.currentRoute.value.path === '/') {
                            const el = document.getElementById(hash)
                            if (el) {
                                el.scrollIntoView({ behavior: 'smooth', block: 'center' })
                                el.classList.add('highlight-ticket')
                                setTimeout(() => el.classList.remove('highlight-ticket'), 2000)
                            } else {
                                await router.push(`/#${hash}`)
                            }
                        } else {
                            await router.push(`/#${hash}`)
                        }
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
