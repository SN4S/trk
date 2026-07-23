<template>
  <div class="chat_block">
    <div class="messageArea" ref="messageAreaRef" @scroll="handleScroll">
      <template v-for="item in feed" :key="`${item.type}-${item.id}`">
        <div class="massage_block" :style="`justify-content: ${item.data.user?.username === currentUser?.username ? 'end' : ''}`" v-if="item.type === 'reply'">
          <chat-message  :id="`reply-${item.data.id}`" :message="item.data" :is-me="item.data.user?.username === currentUser?.username" :is-group-mode="true">
            <template #ticket_slot>
              <div class="parent-ticket-link">
                <a :href="`#ticket-${item.data.ticket_id}`">#{{ item.data.ticket?.ticket_num || item.data.ticket_id }}</a>
              </div>
            </template>
            <template #controls>
                <button v-if="item.data.ticket?.status !== 'closed'" class="control-btn" @click="doReply(item.data.ticket, item.data)">↩ Відповісти</button>
  <!--              <button class="control-btn" @click="doForward('reply', item.data.ticket_id, item.data.id)">➦ В глобальний чат</button>-->
                <button v-if="currentUser?.role === 'admin' || currentUser?.role === 'manager'" class="control-btn" @click="doAssign(tickets.find(t => t.id === item.data.ticket_id)!, item.data)">Призначити</button>
            </template>
          </chat-message>
        </div>
        <div class="massage_block " v-else>
          <chat-ticket
              
              :id="`ticket-${item.data.id}`"
              :ticket="item.data"
          >
            <template #controls>
                <button v-if="item.data.status !== 'closed'" class="control-btn" @click="doReply(item.data)">↩ Відповісти</button>
  <!--              <button class="control-btn" @click="doForward('ticket', item.data.id)">➦ В глобальний чат</button>-->
                <button v-if="currentUser?.role === 'admin' || currentUser?.role === 'manager'" class="control-btn" @click="doAssign(item.data)">Призначити</button>
            </template>
          </chat-ticket>
        </div>
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

    <form-popup v-model="assignPopup.show" title="Призначення тікета">
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <form-select
          v-model="assignPopup.userId"
          :options="users.map(u => ({ value: u.id, label: u.username }))"
          placeholder="Нікому"
        />
        <form-button @click="submitAssign">Призначити</form-button>
      </div>
    </form-popup>

    <button v-if="showGoDown" class="goDown" @click="scrollToSection">↓</button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ChatMessage from '~/components/chat/message.vue'
import MessageInput from '~/components/form/messageInput.vue'
import { useTickets, type ApiTicket } from '~/composables/useTickets'
// When not in a group, we can fetch all replies using useRepliesT without a ticketId (if the API supports it)
// or we can use a new global replies composable. Wait, useRepliesG without groupId will fetch what?
import { useRepliesG, type ApiReply } from '~/composables/useReplies'
import { useApi } from '~/composables/useApi'
import { useFilter } from '~/composables/useFilter'

const route = useRoute()
const { apiFetch } = useApi()
const { filter } = useFilter()
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

function doReply(ticket: ApiTicket, reply?: ApiReply) {
  replyingToTicket.value = ticket
  replyingToReply.value = reply || null
  document.getElementById('message-f')?.focus()
}

async function doForward(type: 'ticket' | 'reply', ticketId: number, replyId?: number) {
  try {
    if (type === 'ticket') {
      await apiFetch(`/tickets/${ticketId}/forward`, { method: 'POST' })
    } else if (type === 'reply') {
      await apiFetch(`/tickets/${ticketId}/replies/${replyId}/forward`, { method: 'POST' })
    }
    addToast({ title: 'Успіх', message: "Успішно переслано у глобальний чат", type: 'success' })
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка пересилки', type: 'error' })
  }
}

const assignPopup = ref({
  show: false,
  type: 'ticket' as 'ticket' | 'reply',
  ticket: null as ApiTicket | null,
  reply: null as ApiReply | null,
  userId: null as number | null
})

function doAssign(ticket: ApiTicket, reply?: ApiReply) {
  assignPopup.value.type = reply ? 'reply' : 'ticket'
  assignPopup.value.ticket = ticket
  assignPopup.value.reply = reply || null
  assignPopup.value.userId = reply ? null : (ticket.current_assignment?.assigned_to?.id ?? null)
  assignPopup.value.show = true
}

async function submitAssign() {
  if (!assignPopup.value.ticket) return
  try {
    if (assignPopup.value.type === 'ticket') {
      await apiFetch(`/tickets/${assignPopup.value.ticket.id}/assign`, { 
        method: 'PATCH',
        body: { user_id: assignPopup.value.userId || null }
      })
      fetchTickets() // refresh tickets to reflect assignment
    } else if (assignPopup.value.type === 'reply') {
      if (!assignPopup.value.userId) {
        addToast({ title: 'Увага', message: 'Оберіть користувача', type: 'warning' })
        return
      }
      await apiFetch(`/tickets/${assignPopup.value.ticket.id}/replies/${assignPopup.value.reply!.id}/assign`, {
        method: 'POST',
        body: { user_id: assignPopup.value.userId }
      })
      addToast({ title: 'Успіх', message: "Успішно призначено у глобальний чат", type: 'success' })
    }
    assignPopup.value.show = false
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка призначення', type: 'error' })
  }
}

async function sendMessage(attachmentIds: number[] = []) {
  if (!messageText.value.trim() && attachmentIds.length === 0) return
  if (!replyingToTicket.value) {
    addToast({ title: 'Увага', message: "Будь ласка, виберіть тікет або повідомлення для відповіді (натисніть правою кнопкою миші)", type: 'warning' })
    return
  }
  if (replyingToTicket.value.status === 'closed') {
    addToast({ title: 'Увага', message: "Неможливо відповісти на закритий тікет", type: 'warning' })
    return
  }

  const isPrivate = (document.getElementById('check') as HTMLInputElement)?.checked ?? false

  try {
    await apiFetch(`/tickets/${replyingToTicket.value.id}/replies/`, {
      method: 'POST',
      body: {
        message: messageText.value,
        is_support: !isPrivate,
        requires_client_reply: false,
        reply_to_reply_id: replyingToReply.value?.id || null,
        attachment_ids: attachmentIds
      }
    })
    
    messageText.value = ''
    replyingToTicket.value = null
    replyingToReply.value = null
    
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

.massage_block{
  display: flex;
}

.right {
  justify-content: end;
}

.messageArea {
  flex: 1;
  overflow-y: auto;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.messageLeft img {
  display: block;
  width: 100%;
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
  border: var(--border);
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
