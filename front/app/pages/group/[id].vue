<template>
  <div class="chat_block" @click="closeMenu">
    <div class="messageArea" ref="messageAreaRef" @scroll="handleScroll">
      <template v-for="item in feed" :key="`${item.type}-${item.id}`">
        <chat-message v-if="item.type === 'reply'" :message="item.data" :is-me="item.data.user?.username === currentUser?.username" @contextmenu.prevent="openReplyMenu($event, item.data)">
          <template #extra>
            <div class="parent-ticket-link">
              <a :href="`#ticket-${item.data.ticket_id}`">↑ До тікету #{{ item.data.ticket?.ticket_num || item.data.ticket_id }}</a>
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
      v-model:requiresClientReply="requiresClientReply"
      :replying-to-ticket="replyingToTicket"
      @send="sendMessage"
      @cancel-reply="replyingToTicket = null"
    />

    <!-- Context Menu for "Reply" -->
    <div v-if="menu.show" class="ctx-menu" :style="{ top: menu.y + 'px', left: menu.x + 'px' }" @click.stop>
      <button v-if="menu.type === 'ticket'" class="ctx-item" @click="setReplyTicket">↩ Відповісти</button>
      <div v-if="menu.type === 'ticket'" class="ctx-divider"></div>
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
          ticket: parentTicket ? { id: parentTicket.id, name: '', soc_user_name: parentTicket.soc_user_name, ticket_num: parentTicket.ticket_num } : null
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

  handleScroll()
})

// ── Messaging State & Logic ──────────────────────────────────────────────────
const messageText = ref('')
const replyingToTicket = ref<ApiTicket | null>(null)

const menu = ref({
  show: false,
  x: 0,
  y: 0,
  type: null as 'ticket' | 'reply' | null,
  ticket: null as ApiTicket | null,
  reply: null as ApiReply | null,
})

function openTicketMenu(e: MouseEvent, ticket: ApiTicket) {
  document.removeEventListener('click', closeMenu)
  menu.value = { show: true, x: e.clientX, y: e.clientY, type: 'ticket', ticket, reply: null }
  document.addEventListener('click', closeMenu, { once: true })
}

function openReplyMenu(e: MouseEvent, reply: ApiReply) {
  document.removeEventListener('click', closeMenu)
  menu.value = { show: true, x: e.clientX, y: e.clientY, type: 'reply', ticket: null, reply }
  document.addEventListener('click', closeMenu, { once: true })
}

function closeMenu() {
  menu.value.show = false
}

function setReplyTicket() {
  if (menu.value.ticket) {
    replyingToTicket.value = menu.value.ticket
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
    alert("Успішно переслано у глобальний чат")
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Помилка пересилки')
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
    alert(e?.data?.detail ?? 'Помилка призначення')
  } finally {
    closeMenu()
  }
}

const requiresClientReply = ref(false)

async function sendMessage() {
  if (!replyingToTicket.value) {
    alert("Будь ласка, виберіть тікет для відповіді (натисніть правою кнопкою миші на тікет)")
    return
  }

  try {
    await apiFetch(`/tickets/${replyingToTicket.value.id}/replies/`, {
      method: 'POST',
      body: {
        message: messageText.value,
        is_support: true,
        requires_client_reply: requiresClientReply.value
      }
    })

    // Clear the input and state
    messageText.value = ''
    replyingToTicket.value = null
    requiresClientReply.value = false

    // Refresh the feed
    fetchReplies()
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Помилка надсилання повідомлення')
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
  margin-top: 4px;
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