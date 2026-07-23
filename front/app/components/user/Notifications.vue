<template>
  <div class="notifications-wrapper" @click.stop="toggleDropdown">
    <button class="bell-button">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
        class="bell-icon"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
        />
      </svg>
      <span v-if="unreadCount > 0" class="badge">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <div v-if="showDropdown" class="dropdown-menu" @click.stop>
      <div class="dropdown-header">
        <h3>Сповіщення</h3>
        <button v-if="unreadCount > 0" class="mark-all-btn" @click="markAllAsReadLocally">
          Прочитати всі
        </button>
      </div>

      <div class="dropdown-body">
        <div v-if="pending" class="empty-state">Завантаження...</div>
        <div v-else-if="notifications.length === 0" class="empty-state">
          Немає нових сповіщень
        </div>
        <div v-else class="notification-list">
          <div
            v-for="notif in notifications"
            :key="notif.id"
            class="notification-item"
            :class="{ 'is-read': notif.is_read }"
            @click="handleNotificationClick(notif)"
          >
            <div class="notif-content">
              <span class="notif-title">{{ getNotificationTitle(notif) }}</span>
              <span v-if="getNotificationTheme(notif)" class="notif-theme">{{ getNotificationTheme(notif) }}</span>
              <span class="notif-desc">{{ getNotificationDesc(notif) }}</span>
            </div>
            <div class="notif-time">{{ formatTime(notif.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifications, type ApiNotification } from '~/composables/useNotifications'

const { notifications, pending, initNotifications, markAsRead } = useNotifications()
const router = useRouter()

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

// Initializes fetch and WS listeners on mount
initNotifications()

const showDropdown = ref(false)

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function closeDropdown() {
  showDropdown.value = false
}

// Close on outside click
onMounted(() => {
  document.addEventListener('click', closeDropdown)
})
onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

function getNotificationTitle(notif: ApiNotification) {
  const groupName = notif.data?.group?.name || notif.data?.group_name
  const ticketNum = notif.data?.ticket_num || notif.data?.ticket?.ticket_num

  if (notif.type === 'assign_ticket') {
    return ticketNum ? `Тікет - ${ticketNum}` : 'Призначення тікета'
  }

  if (notif.type === 'status_change') {
    return ticketNum ? `Тікет - ${ticketNum}` : 'Зміна статусу'
  }

  if (notif.type === 'new_general_message') return 'Загальний чат'
  
  if (groupName) {
    return ticketNum ? `${groupName} - ${ticketNum}` : groupName
  }

  return ticketNum ? `Тікет - ${ticketNum}` : 'Сповіщення'
}

function getNotificationTheme(notif: ApiNotification) {
  if (notif.type === 'new_ticket' || notif.type === 'new_reply' || notif.type === 'status_change') {
    return notif.data?.theme?.name || notif.data?.theme_name || notif.data?.ticket?.theme?.name || null
  }
  return null
}

function getNotificationDesc(notif: ApiNotification) {
  if (notif.type === 'new_ticket') {
    return `Новий тікет: ${notif.data?.message || ''}`
  }
  if (notif.type === 'status_change' || notif.type === 'update_ticket') {
    const statusMap: Record<string, string> = {
      open: 'відкритий',
      pending: 'в роботі',
      closed: 'закритий'
    }
    const rawStatus = notif.data?.status
    const status = rawStatus ? (statusMap[rawStatus] || rawStatus) : 'оновлено'
    return `Оновлення статусу: ${status}`
  }
  if (notif.type === 'assign_ticket') {
    const assignedTo = notif.data?.current_assignment?.assigned_to?.username || 'Вас'
    return `Призначення тікета: на ${assignedTo}`
  }
  if (notif.type === 'new_reply') {
    return `Нове повідомлення: ${notif.data?.message || ''}`
  }
  if (notif.type === 'new_general_message') {
    const author = notif.data?.user?.username || 'Колега'
    return `Нове повідомлення від ${author}: ${notif.data?.message || ''}`
  }
  return ''
}

function formatTime(isoString: string) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function handleNotificationClick(notif: ApiNotification) {
  await markAsRead(notif.id)
  showDropdown.value = false
  
  if (notif.type === 'new_general_message') {
    router.push(`/general#reply-${notif.data?.id || ''}`)
  } else if (notif.type === 'new_reply') {
    if (notif.data?.group_id) {
       router.push(`/group/${notif.data.group_id}#reply-${notif.data.id}`)
    } else if (notif.data?.ticket?.group_id) {
       router.push(`/group/${notif.data.ticket.group_id}#reply-${notif.data.id}`)
    } else {
       router.push(`/#reply-${notif.data?.id || ''}`)
    }
  } else if (['new_ticket', 'update_ticket', 'assign_ticket', 'status_change'].includes(notif.type)) {
    const ticketId = notif.data?.id
    if (notif.data?.group_id) {
       router.push(`/group/${notif.data.group_id}#ticket-${ticketId}`)
    } else {
       router.push(`/#ticket-${ticketId}`)
    }
  }
}

async function markAllAsReadLocally() {
  // Ideally, call an API to mark all as read. For now, mark them one by one.
  const toMark = notifications.value.filter(n => !n.is_read)
  for (const n of toMark) {
    await markAsRead(n.id)
  }
  showDropdown.value = false
}
</script>

<style scoped>
.notifications-wrapper {
  position: relative;
  display: inline-block;
}

.bell-button {
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  padding: 6px;
  color: var(--message-time-color);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s, color 0.2s;
}

.bell-button:hover {
  background-color: var(--nav-item-bg-hover-color);
  color: var(--message-text-color);
}

.bell-icon {
  width: 22px;
  height: 22px;
}

.badge {
  position: absolute;
  top: 0px;
  right: 0px;
  background-color: #e05252;
  color: white;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  padding: 2px 5px;
  line-height: 1;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 320px;
  background-color: var(--message-bg-color);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  max-height: 400px;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background-color: var(--nav-bar-bg);
}

.dropdown-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--message-text-color);
}

.mark-all-btn {
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.mark-all-btn:hover {
  text-decoration: underline;
}

.dropdown-body {
  overflow-y: auto;
  flex: 1;
}

.empty-state {
  padding: 32px 16px;
  text-align: center;
  color: var(--message-time-color);
  font-size: 13px;
}

.notification-list {
  display: flex;
  flex-direction: column;
}

.notification-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  gap: 12px;
}

.notification-item.is-read {
  opacity: 0.6;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background-color: var(--nav-item-bg-hover-color);
}

.notif-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow: hidden;
}

.notif-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--message-text-color);
}

.notif-theme {
  font-size: 12px;
  font-weight: 500;
  color: var(--accent, #e05252);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notif-desc {
  font-size: 12px;
  color: var(--message-time-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notif-time {
  font-size: 11px;
  color: var(--message-time-color);
  white-space: nowrap;
}
</style>
