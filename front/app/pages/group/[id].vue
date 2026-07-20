<template>
  <div class="chat_block" @click="closeMenu">
    <div class="messageArea" ref="messageAreaRef" @scroll="handleScroll">
      <template v-for="item in feed" :key="`${item.type}-${item.id}`">
        <chat-message v-if="item.type === 'reply'" :id="`reply-${item.data.id}`" :message="item.data" :is-me="item.data.user?.username === currentUser?.username" :is-group-mode="true" @contextmenu.prevent="openReplyMenu($event, item.data)">
          <template #ticket_slot>
            <div class="parent-ticket-link">
              <a :href="`#ticket-${item.data.ticket_id}`">#{{ item.data.ticket?.ticket_num || item.data.ticket_id }}</a>
            </div>
          </template>
        </chat-message>
        <chat-ticket 
          v-else 
          :id="`ticket-${item.data.id}`"
          :ticket="item.data" 
          @contextmenu="openTicketMenu($event, item.data)"
        />
      </template>

      <div v-if="pending" class="state-msg">Завантаження…</div>
      <div v-else-if="error" class="state-msg error">{{ error }}</div>
      <div v-else-if="feed.length === 0" class="state-msg muted">Тікети не знайдені</div>

      <div id="bottom"></div>
    </div>
    
    <message-input 
      v-model="messageText"
      :replying-to-ticket="replyingToTicket"
      :replying-to-message="replyingToReply ? { sender: replyingToReply.user?.username || replyingToReply.ticket?.soc_user_name || 'User', text: replyingToReply.message } : null"
      @send="sendMessage"
      @cancel-reply="cancelReply"
    />

    <!-- Context Menu for "Reply" -->
    <div v-if="menu.show" class="ctx-menu" :style="{ top: menu.y + 'px', left: menu.x + 'px' }" @click.stop>
      <button v-if="menu.ticket?.status !== 'closed'" class="ctx-item" @click="setReplyTicket">↩ Відповісти</button>
      <button class="ctx-item" @click="forwardActiveItem">➦ В глобальний чат</button>

      <template v-if="menu.type === 'ticket' && (currentUser?.role === 'admin' || currentUser?.role === 'manager')">
        <div class="ctx-divider"></div>
        <div class="ctx-header">Призначити:</div>
        <form-select
            class="ctx-assign-select"
            :model-value="menu.ticket?.current_assignment?.assigned_to?.id ?? null"
            :options="users.map(u => ({ value: u.id, label: u.username }))"
            placeholder="Нікому"
            size="small"
            @update:model-value="v => assignTicket(v || null)"
        />
      </template>
    </div>

    <button v-if="showGoDown" class="goDown" @click="scrollToSection">↓</button>
  </div>
</template>

<script setup lang="ts">

import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ChatMessage from '~/components/chat/message.vue'
import MessageInput from '~/components/form/messageInput.vue'
import { useTickets, type ApiTicket } from '~/composables/useTickets'
import { useRepliesG, type ApiReply } from '~/composables/useReplies'
import { useApi } from '~/composables/useApi'

const route = useRoute()
const { apiFetch } = useApi()
const { currentUser } = useAuth()
const { addToast } = useToast()

const users = ref<any[]>([])
async function fetchUsers() {
  if (currentUser.value?.role === 'admin' || currentUser.value?.role === 'manager') {
    try {
      users.value = await apiFetch<any[]>('/auth/users')
    } catch (e) {
      console.error(e)
    }
  }
}
onMounted(fetchUsers)

const groupId = computed(() => {
  const parsed = parseInt(route.params.id as string, 10)
  return isNaN(parsed) ? null : parsed
})

// ── Scroll state ──────────────────────────────────────────────────────────
const messageAreaRef = ref<HTMLElement | null>(null)

const showGoDown = ref(false)
const NEAR_BOTTOM_PX = 80

function isNearBottom(el: HTMLElement) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_PX
}

function handleScroll() {
  const el = messageAreaRef.value
  if (!el) return
  showGoDown.value = !isNearBottom(el)
}

function scrollToSection() {
  document.getElementById('bottom')?.scrollIntoView({ behavior: 'smooth' })
}

// Fetch tickets scoped to this group — filters are sent to the API automatically
// by the composable's internal watcher (search, status, themeId changes trigger refetch)
const { tickets, pending: ticketsPending, error: ticketsError, fetchTickets } = useTickets(groupId)

const { replies, pending: repliesPending, error: repliesError, fetchReplies } = useRepliesG(groupId)

type FeedItem =
    | { type: 'reply'; ts: number; id: number; data: ApiReply }
    | { type: 'ticket'; ts: number; id: number; data: ApiTicket }

const feed = computed<FeedItem[]>(() => {
  const replyItems: FeedItem[] = replies.value
    .filter(r => tickets.value.some(t => t.id === r.ticket_id))
    .map(r => {
      const parentTicket = tickets.value.find(t => t.id === r.ticket_id)
      return {
        type: 'reply',
        ts: new Date(r.created_at).getTime(),
        id: r.id,
        data: {
          ...r,
          ticket: parentTicket ? { id: parentTicket.id, name: '', soc_user_name: parentTicket.soc_user_name, ticket_num: parentTicket.ticket_num, message: parentTicket.message, theme: parentTicket.theme, status: parentTicket.status } : null
        } as any,
      }
  })

  const ticketItems: FeedItem[] = tickets.value.map(t => ({
    type: 'ticket',
    ts: new Date(t.created_at).getTime(),
    id: t.id,
    data: t,
  }))

  return [...replyItems, ...ticketItems].sort((a, b) => a.ts - b.ts)
})

const pending = computed(() => ticketsPending.value || repliesPending.value)
const error = computed(() => ticketsError.value || repliesError.value)

// Always jump to bottom once loading finishes (new group, new messages, everything)
// unless a deep-link hash targets a specific ticket.
watch(pending, async (newVal) => {
  if (newVal) return
  await nextTick()
  scrollToHash()
  handleScroll()
})

watch(() => route.hash, () => {
  scrollToHash()
})

function scrollToHash() {
  if (route.hash) {
    const target = document.querySelector(route.hash)
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' })
      target.classList.add('highlight-ticket')
      setTimeout(() => target.classList.remove('highlight-ticket'), 2000)
    }
  } else {
    document.getElementById('bottom')?.scrollIntoView()
  }
}

// ── Messaging State & Logic ──────────────────────────────────────────────────
const messageText = ref('')
const replyingToTicket = ref<ApiTicket | null>(null)
const replyingToReply = ref<ApiReply | null>(null)

function cancelReply() {
  replyingToTicket.value = null
  replyingToReply.value = null
}

const menu = ref({
  show: false,
  x: 0,
  y: 0,
  type: null as 'ticket' | 'reply' | null,
  ticket: null as ApiTicket | null,
  reply: null as ApiReply | null,
})

async function openTicketMenu(e: MouseEvent, ticket: ApiTicket) {
  document.removeEventListener('click', closeMenu)
  let x = e.clientX
  let y = e.clientY
  menu.value = { show: true, x, y, type: 'ticket', ticket, reply: null }
  
  await nextTick()
  const menuEl = document.querySelector('.ctx-menu') as HTMLElement
  if (menuEl) {
    const rect = menuEl.getBoundingClientRect()
    if (x + rect.width > window.innerWidth) x = window.innerWidth - rect.width - 10
    if (y + rect.height > window.innerHeight) y = window.innerHeight - rect.height - 10
    menu.value.x = x
    menu.value.y = y
  }

  document.addEventListener('click', closeMenu, { once: true })
}

async function openReplyMenu(e: MouseEvent, reply: any) {
  document.removeEventListener('click', closeMenu)
  let x = e.clientX
  let y = e.clientY
  menu.value = { show: true, x, y, type: 'reply', ticket: reply.ticket as ApiTicket, reply }
  
  await nextTick()
  const menuEl = document.querySelector('.ctx-menu') as HTMLElement
  if (menuEl) {
    const rect = menuEl.getBoundingClientRect()
    if (x + rect.width > window.innerWidth) x = window.innerWidth - rect.width - 10
    if (y + rect.height > window.innerHeight) y = window.innerHeight - rect.height - 10
    menu.value.x = x
    menu.value.y = y
  }

  document.addEventListener('click', closeMenu, { once: true })
}

function closeMenu() {
  menu.value.show = false
}

function setReplyTicket() {
  if (menu.value.reply) {
    replyingToReply.value = menu.value.reply
    replyingToTicket.value = menu.value.ticket
  } else if (menu.value.ticket) {
    replyingToTicket.value = menu.value.ticket
    replyingToReply.value = null
  }
  closeMenu()
  // Focus the input
  document.getElementById('message-f')?.focus()
}

async function forwardActiveItem() {
  try {
    if (menu.value.type === 'ticket' && menu.value.ticket) {
      await apiFetch(`/tickets/${menu.value.ticket.id}/forward`, { method: 'POST' })
    } else if (menu.value.type === 'reply' && menu.value.reply) {
      await apiFetch(`/tickets/${menu.value.reply.ticket_id}/replies/${menu.value.reply.id}/forward`, { method: 'POST' })
    }
    addToast({ title: 'Успіх', message: "Успішно переслано у глобальний чат", type: 'success' })
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка пересилки', type: 'error' })
  } finally {
    closeMenu()
  }
}

async function assignTicket(userId: number | null) {
  if (!menu.value.ticket) return
  try {
    await apiFetch(`/tickets/${menu.value.ticket.id}/assign`, {
      method: 'PATCH',
      body: { user_id: userId }
    })
    fetchTickets() // refresh tickets to reflect assignment
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка призначення', type: 'error' })
  } finally {
    closeMenu()
  }
}

async function sendMessage() {
  if (!replyingToTicket.value) {
    addToast({ title: 'Увага', message: "Будь ласка, виберіть тікет для відповіді (натисніть правою кнопкою миші на тікет)", type: 'warning' })
    return
  }
  if (replyingToTicket.value.status === 'closed') {
    addToast({ title: 'Увага', message: "Неможливо відповісти на закритий тікет", type: 'warning' })
    return
  }

  try {
    await apiFetch(`/tickets/${replyingToTicket.value.id}/replies/`, {
      method: 'POST',
      body: {
        message: messageText.value,
        is_support: true,
        requires_client_reply: false,
        reply_to_reply_id: replyingToReply.value?.id || null
      }
    })

    // Clear the input and state
    messageText.value = ''
    replyingToTicket.value = null
    replyingToReply.value = null

    // Refresh the feed
    fetchReplies()
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка надсилання повідомлення', type: 'error' })
  }
}

</script>

<style scoped>
.chat_block {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.messageArea {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Context Menu */
.ctx-menu {
  position: fixed;
  background: var(--message-bg-color);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 0;
  min-width: 140px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 9999;
}
.ctx-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 6px 16px;
  background: none;
  border: none;
  color: var(--message-text-color);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.1s;
}
.ctx-item:hover {
  background: var(--nav-item-bg-hover-color);
}
.ctx-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}
.ctx-header {
  padding: 4px 16px;
  font-size: 11px;
  color: var(--message-time-color);
  font-weight: bold;
  text-transform: uppercase;
}

.parent-ticket-link {
  font-size: 11px;
  opacity: 0.8;
}

.parent-ticket-link a {
  color: inherit;
  text-decoration: underline;
  transition: opacity 0.2s;
}

.parent-ticket-link a:hover {
  opacity: 0.6;
}

.highlight-ticket {
  animation: highlight 2s ease-out;
}

.goDown {
  position: absolute;
  right: 20px;
  bottom: 90px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--message-bg-color);
  color: var(--message-text-color);
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  z-index: 5;
}
.goDown:hover {
  background: var(--nav-item-bg-hover-color);
}

@keyframes highlight {
  0% { box-shadow: 0 0 0 4px var(--accent); }
  100% { box-shadow: 0 0 0 0px transparent; }
}
</style>