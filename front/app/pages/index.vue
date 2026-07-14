<template>
  <div class="chat_block" @click="closeMenu">
    <div class="messageArea">
      <template v-for="item in feed" :key="`${item.type}-${item.id}`">
        <chat-message v-if="item.type === 'reply'" :message="item.data" :is-me="item.data.user?.username==currentUser?.username">
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
    </div>
    
    <message-input 
      v-model="messageText"
      v-model:requiresClientReply="requiresClientReply"
      :replying-to-ticket="replyingToTicket"
      @send="sendMessage"
      @cancel-reply="replyingToTicket = null"
    />

    <!-- Context Menu for "Reply" -->
    <div 
      v-if="menu.show" 
      class="ctx-menu" 
      :style="{ top: menu.y + 'px', left: menu.x + 'px' }"
      @click.stop
    >
      <button 
        class="ctx-item"
        @click="setReplyTicket"
      >
        ↩ Відповісти
      </button>
      <div class="ctx-divider"></div>
      <button 
        class="ctx-item"
        @click="forwardToGeneralChat"
      >
        ➦ В глобальний чат
      </button>

      <template v-if="currentUser?.role === 'admin' || currentUser?.role === 'manager'">
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
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ChatMessage from '~/components/chat/message.vue'
import MessageInput from '~/components/form/messageInput.vue'
import { useTickets, type ApiTicket } from '~/composables/useTickets'
// When not in a group, we can fetch all replies using useRepliesT without a ticketId (if the API supports it)
// or we can use a new global replies composable. Wait, useRepliesG without groupId will fetch what?
import { useRepliesG, type ApiReply } from '~/composables/useReplies'
import { useApi } from '~/composables/useApi'
import { useFilter } from '~/composables/useFilter'

const { apiFetch } = useApi()
const { filter } = useFilter()
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

// Fetch tickets not scoped to any group (global)
const { tickets, pending: ticketsPending, error: ticketsError, fetchTickets } = useTickets()

// Fetch replies not scoped to any group. 
// We use useRepliesG with no groupId (undefined) which won't pass group_id param, so it should fetch all replies.
const { replies, pending: repliesPending, error: repliesError, fetchReplies } = useRepliesG()

type FeedItem =
    | { type: 'reply'; ts: number; id: number; data: ApiReply }
    | { type: 'ticket'; ts: number; id: number; data: ApiTicket }

const feed = computed<FeedItem[]>(() => {
  // If no search and no filter, we might not want to show all global messages to avoid overwhelming?
  // Actually, the user says "it should work for every messsage unless group selected." 
  // Let's just show the global feed.
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

import { nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()

watch(pending, async (newVal) => {
  if (!newVal) {
    await nextTick()
    if (route.hash) {
      const el = document.querySelector(route.hash)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        el.classList.add('highlight-ticket')
        setTimeout(() => el.classList.remove('highlight-ticket'), 2000)
      }
    }
  }
})

// ── Messaging State & Logic ──────────────────────────────────────────────────
const messageText = ref('')
const replyingToTicket = ref<ApiTicket | null>(null)

const menu = ref({
  show: false,
  x: 0,
  y: 0,
  ticket: null as ApiTicket | null
})

function openTicketMenu(e: MouseEvent, ticket: ApiTicket) {
  menu.value = {
    show: true,
    x: e.clientX,
    y: e.clientY,
    ticket
  }
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
  document.getElementById('message-f')?.focus()
}

async function forwardToGeneralChat() {
  if (!menu.value.ticket) return
  try {
    await apiFetch(`/tickets/${menu.value.ticket.id}/forward`, { method: 'POST' })
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

  const isPrivate = (document.getElementById('check') as HTMLInputElement)?.checked ?? false

  try {
    await apiFetch(`/tickets/${replyingToTicket.value.id}/replies/`, {
      method: 'POST',
      body: {
        message: messageText.value,
        is_support: !isPrivate,
        requires_client_reply: requiresClientReply.value
      }
    })
    
    messageText.value = ''
    replyingToTicket.value = null
    
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
  border: 1px solid var(--border-color);
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
  background: var(--border-color);
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

@keyframes highlight {
  0% { box-shadow: 0 0 0 4px var(--accent); }
  100% { box-shadow: 0 0 0 0px transparent; }
}
</style>
