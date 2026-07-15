<template>
  <div class="chat_block">
    <div class="messageArea" ref="messageAreaRef" @scroll="handleScroll">
      <div v-if="pending" class="state-msg">Завантаження…</div>
      <div v-else-if="error" class="state-msg error">{{ error }}</div>
      <div v-else-if="mappedMessages.length === 0" class="state-msg muted">Повідомлень немає</div>

      <chat-message
          v-else
          v-for="msg in mappedMessages"
          :key="msg.id"
          :id="'msg-' + msg.id"
          :message="msg"
          :is-me="msg.is_support"
          :sender-name="msg.user?.username || 'Support'"
          :hide-text="!!msg.ticket"
          @contextmenu.prevent="openMsgMenu($event, msg)"
      >
        <template #extra>
          <div v-if="msg.parent" class="reply-quote" @click="scrollToMessage(msg.parent.id)">
            <span class="reply-quote-user">{{ msg.parent.user?.username || 'Support' }}</span>
            <span class="reply-quote-text">{{ msg.parent.message }}</span>
          </div>
          <div v-if="msg.ticket && !msg.reply" class="forwarded-message">
            <span class="forward-label">↪ Переслано тікет від {{ msg.ticket.soc_user_name }}</span>
            <div class="reply-quote">
              <span class="reply-quote-user">Тікет #{{ msg.ticket.ticket_num }}</span>
              <span class="reply-quote-text">{{ msg.ticket.message || 'Без тексту' }}</span>
            </div>
            <div class="card-actions">
              <NuxtLink :to="`/group/${msg.ticket.group_id}#ticket-${msg.ticket_id}`" class="action-btn">
                Відкрити тікет
              </NuxtLink>
            </div>
          </div>
          <div v-if="msg.reply" class="forwarded-message">
            <span class="forward-label">↪ Переслано з тікету #{{ msg.ticket?.ticket_num }}</span>
            <div class="reply-quote">
              <span class="reply-quote-user">{{ msg.reply.user?.username || 'Support' }}</span>
              <span class="reply-quote-text">{{ msg.reply.message }}</span>
            </div>
            <div class="card-actions">
              <NuxtLink :to="`/group/${msg.ticket?.group_id}#ticket-${msg.ticket_id}`" class="action-btn">
                Відкрити тікет
              </NuxtLink>
            </div>
          </div>
        </template>
      </chat-message>

      <div v-if="menu.show" class="ctx-menu" :style="{ top: menu.y + 'px', left: menu.x + 'px' }" @click.stop>
        <button class="ctx-item" @click="setReply(menu.msg)">↩ Відповісти</button>
      </div>

      <div id="bottom"></div>
    </div>


    <!-- Message Input -->
    <div class="input-area">
      <message-input
          v-model="messageText"
          hide-checkbox
          :replying-to-message="replyingTo"
          @send="sendMessage"
          @cancel-reply="replyingTo = null"
      />
    </div>

    <button v-if="showGoDown" class="goDown" @click="scrollToSection">↓</button>

  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed, watch, nextTick} from 'vue'
import { useApi } from '~/composables/useApi'
import { useAuth } from '~/composables/useAuth'
import { useFilter } from '~/composables/useFilter'
import MessageInput from '~/components/form/messageInput.vue'
import ChatMessage from '~/components/chat/message.vue'
import {useRoute} from "#vue-router";

const { apiFetch } = useApi()
const { currentUser } = useAuth()
const route = useRoute()

const messages = ref<any[]>([])
const pending = ref(false)
const error = ref('')

const messageText = ref('')

const { filter } = useFilter()

const mappedMessages = computed(() => {
  let list = messages.value
  
  const q = filter.search?.toLowerCase().trim()
  if (q) {
    list = list.filter(msg => {
      const textMatch = msg.message?.toLowerCase().includes(q)
      const userMatch = msg.user?.username?.toLowerCase().includes(q)
      let ticketMatch = false
      if (msg.ticket) {
        ticketMatch = 
          msg.ticket.ticket_num?.toLowerCase().includes(q) ||
          msg.ticket.theme?.name?.toLowerCase().includes(q) ||
          msg.ticket.group?.name?.toLowerCase().includes(q) ||
          msg.ticket.soc_user_name?.toLowerCase().includes(q)
      }
      return textMatch || userMatch || ticketMatch
    })
  }

  return list.map(msg => ({
    id: msg.id,
    ticket_id: msg.ticket_id,
    message: msg.message,
    is_support: currentUser.value ? msg.user_id === currentUser.value.id : false,
    user_id: msg.user_id,
    created_at: msg.created_at,
    user: msg.user,
    ticket: msg.ticket,
    reply: msg.reply,
    parent: msg.parent
  }))
})

async function loadMessages() {
  pending.value = true
  error.value = ''
  try {
    const data = await apiFetch('/general-chat/messages')
    messages.value = data
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Помилка завантаження'
  } finally {
    pending.value = false
  }
}

onMounted(() => {
  loadMessages()
})

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

const menu = ref({ show: false, x: 0, y: 0, msg: null as any })
function openMsgMenu(e: MouseEvent, msg: any) {
  menu.value = { show: true, x: e.clientX, y: e.clientY, msg }
  document.addEventListener('click', closeCtxMenu, { once: true })
}
function closeCtxMenu() { menu.value.show = false }

const replyingTo = ref<{ id: number; sender: string; text: string } | null>(null)
function setReply(msg: any) {
  if (!msg) return
  replyingTo.value = { id: msg.id, sender: msg.user?.username || 'Support', text: msg.message }
  closeCtxMenu()
  document.getElementById('message-f')?.focus()
}

function scrollToMessage(id: number | null | undefined) {
  if (!id) return
  const el = document.getElementById('msg-' + id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-message')
    setTimeout(() => el.classList.remove('highlight-message'), 2000)
  }
}

async function sendMessage() {
  if (!messageText.value.trim()) return
  try {
    await apiFetch('/general-chat/messages', {
      method: 'POST',
      body: { message: messageText.value, parent_id: replyingTo.value?.id ?? null }
    })
    messageText.value = ''
    replyingTo.value = null
    loadMessages()
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
.state-msg {
  text-align: center;
  padding: 20px;
  color: var(--message-time-color);
}
.state-msg.error { color: #e05252; }
.forwarded-message {
  margin-top: 4px;
  margin-bottom: 4px;
}
.forward-label {
  display: block;
  font-size: 11px;
  color: var(--accent);
  margin-bottom: 2px;
  font-weight: 500;
  opacity: 0.9;
}
.message_out .forward-label {
  color: #fff;
}
.card-actions {
  margin-top: 4px;
  display: flex;
  justify-content: flex-start;
}
.action-btn {
  display: inline-block;
  background: rgba(0, 0, 0, 0.05);
  color: inherit;
  padding: 4px 8px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  font-size: 11px;
  border: 1px solid rgba(0,0,0,0.1);
  transition: all 0.2s;
}
.message_out .action-btn {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}
.action-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  text-decoration: none;
}
.message_out .action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}
.input-area {
  flex-shrink: 0;
}

.reply-quote { border-left: 3px solid var(--accent); padding-left: 8px; margin-top: 4px; font-size: 12px; opacity: 0.85; cursor: pointer; transition: opacity 0.2s; }
.reply-quote:hover { opacity: 1; }
.reply-quote-user { display: block; font-weight: 600; color: var(--accent); }
.reply-quote-text { display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }

.highlight-message {
  animation: highlight 2s ease-out;
}
@keyframes highlight {
  0% { box-shadow: 0 0 0 4px var(--accent); }
  100% { box-shadow: 0 0 0 0px transparent; }
}
</style>
