<template>
  <div class="message" :class="{'message_out': alignRight, 'not_tg': message.is_support && !message.tg_message_id}">
    <!-- Start Status -->
    <chat-ticket-status v-if="isGroupMode && message.ticket" :status="message.ticket.status" :interactive="true" @update="changeStatus" />
    <!-- / Status -->
    <!-- Start Sender -->
    <p class="message_sender" :style="isGroupMode && message.ticket ? (alignRight ? 'padding-left: 60px;' : 'padding-right: 60px;') : ''">
      {{ displayName }}
    </p>
    <!-- / Sender -->
    <!-- Start Reply -->
    <div v-if="message.parent_reply" class="message_parent clickable" @click="scrollToElement('reply', message.parent_reply.id)">
      <span class="parent_sender">{{ message.parent_reply.user?.username || 'User' }}</span>
      <span class="parent_text">{{ message.parent_reply.message.length > 50 ? message.parent_reply.message.slice(0, 50) + '...' : message.parent_reply.message }}</span>
    </div>
    <div v-else-if="message.ticket" class="message_parent clickable" @click="scrollToElement('ticket', message.ticket.id || message.ticket_id)">
      <span class="parent_sender">Тікет #{{ message.ticket.ticket_num || message.ticket_id }}</span>
      <span class="parent_text" v-if="message.ticket.message">{{ message.ticket.message.length > 50 ? message.ticket.message.slice(0, 50) + '...' : message.ticket.message }}</span>
      <span class="parent_text" v-else>Новий тікет</span>
    </div>
     <!-- / Reply -->
     <!-- Strat Info -->
    <template  v-if="isGroupMode && message.ticket">
      <div class="ticket_inf">
      <p><span class="lable">Тема:</span> {{ message.ticket.theme?.name || 'Без теми' }}</p>
      <p class="ticket_number"><span class="lable">Номер звернення:</span> {{message.ticket.ticket_num || message.ticket.id}}</p>
      </div>
    </template>
     <!-- Strat Info -->
     <!-- Start Text -->
    <p class="message_text" v-if="!hideText" v-html="renderedText"></p>
     <!-- Start Text -->
    <!-- Start Image -->
    <div v-if="message.attachments && message.attachments.length > 0" class="attachments-list">
      <template v-for="att in message.attachments" :key="att.id">
        <a v-if="att.content_type.startsWith('image/')" :href="baseURL + att.file_url" target="_blank" class="attachment-img-link">
          <img :src="baseURL + att.file_url" :alt="att.filename" class="attachment-img" />
        </a>
        <a v-else :href="baseURL + att.file_url" target="_blank" class="attachment-file-link">
          📎 {{ att.filename }}
        </a>
      </template>
    </div>
    <!-- / Image -->
    <!-- Start Date -->
    <slot name="extra"></slot>
    <div class="message_footer">
      <slot name="ticket_slot"></slot>
      <span class="message_time">{{ formattedTime }}</span>
    </div>
    <!-- / Date -->
    <!-- Start Button -->
    <div class="controls msg-controls">
      <slot name="controls">

      </slot>
      <button v-if="!hideText && message.message" class="control-btn" @click="copyMessageText" title="Копіювати">📋 Копіювати</button>
    </div>
    <!-- / Button -->
   <div v-if="!isMe" class="messageLeft">
      <img src="@/assets/img/background/left.png" alt="">
    </div>
    <div v-else class="messageRight">
      <img src="@/assets/img/background/right.png" alt="">
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiReply } from '~/composables/useReplies'
const baseURL = useRuntimeConfig().public.apiBase as string

const props = defineProps<{
  message: ApiReply
  isMe?: boolean | null
  senderName?: string
  hideText?: boolean
  ticket_link?: boolean
  isGroupMode?: boolean
}>()

const alignRight = computed(() => {
  if (props.isMe !== undefined && props.isMe !== null) return props.isMe
  return props.message.is_support
})

const displayName = computed(() => {
  if (props.senderName !== undefined) return props.senderName
  if (props.message.is_support) return props.message.user?.username || 'Support'
  return props.message.ticket?.soc_user_name || 'User'
})

const formattedTime = computed(() => {
  const s = props.message.created_at
  const d = new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z')
  const now = new Date()
  const isToday = d.getDate() === now.getDate() && 
                  d.getMonth() === now.getMonth() && 
                  d.getFullYear() === now.getFullYear()
  const timeStr = d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
  if (isToday) {
    return timeStr
  }
  return `${d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit', year: '2-digit' })} ${timeStr}`
})

import { useMentionableUsers } from '~/composables/useMentionableUsers'
const { users: mentionableUsers } = useMentionableUsers()

function escapeHtml(str: string) {
  return str.replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' } as Record<string,string>)[c])
}

const renderedText = computed(() => {
  const escaped = escapeHtml(props.message.message)
  return escaped.replace(/@\[(\d+):([^\]]+)\]/g, (_m, id: string, storedName: string) => {
    const uid = Number(id)
    const live = mentionableUsers.value.find(u => u.id === uid)
    const display = live?.username ?? storedName
    return `<span class="mention">@${escapeHtml(display)}</span>`
  })
})

function scrollToElement(type: 'ticket' | 'reply', id: number | string) {
  const elId = `${type}-${id}`
  const el = document.getElementById(elId)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-ticket')
    setTimeout(() => el.classList.remove('highlight-ticket'), 2000)
  }
}

import { useApi } from '~/composables/useApi'
const { apiFetch } = useApi()
const { addToast } = useToast()

async function changeStatus(newStatus: string) {
  if (!props.isGroupMode || !props.message.ticket) return
  try {
    await apiFetch(`/tickets/${props.message.ticket.id || props.message.ticket_id}`, {
      method: 'PATCH',
      body: { status: newStatus }
    })
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка оновлення статусу', type: 'error' })
  }
}

async function copyMessageText() {
  try {
    await navigator.clipboard.writeText(props.message.message)
    addToast({ title: 'Скопійовано', message: 'Текст скопійовано в буфер обміну', type: 'success' })
  } catch (e) {
    addToast({ title: 'Помилка', message: 'Не вдалося скопіювати текст', type: 'error' })
  }
}
</script>

<style scoped>
.message {
  position: relative;
  display: flex;
  align-self: flex-start;
  flex-direction: column;
  min-width: 80px;
  max-width: 60%;
  padding: 8px 12px;
  border-radius: 20px;
  background: var(--message-bg-color);
}

.message.not_tg{
  background-color: #eceaea;
}

.ticket_inf {
  margin-bottom: 1rem;
}

.message_sender{
  color: var(--accent);
  margin-bottom: 4px ;
  font-weight: bold;
}

.message_out .message_sender{
  color: var(--second-test-color);
  align-self: flex-end;
}

.message_text {
  margin: 0;
  word-break: break-word;
  white-space: pre-wrap;
}

.message_out {
  align-self: flex-end;
  background: var(--nav-item-bg-active-color);
  color: #fff;
}

.message_out.not_tg {
  background: #29759a; /* Slightly greyer and muted */
}

.message_out :deep(.status-wrapper) {
  right: auto;
  left: 12px;
}
.message_out :deep(.status-popup) {
  right: auto;
  left: 0;
}

.message_footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  width: 100%;
}

.message_time {
  font-size: 11px;
  color: var(--message-time-color);
  user-select: none;
}

.msg-controls {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
  opacity: 0.7;
}

:deep(.control-btn) {
  box-sizing: border-box;
  height: 24px;
  padding: 0 8px;
  font-size: 11px;
  line-height: 22px;
  border-radius: var(--radius);
  background: var(--nav-bar-bg);
  color: var(--message-text-color);
  border: var(--border);
  cursor: pointer;
  transition: all 0.2s;
}

:deep(.control-btn:hover) {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}


.attachments-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.attachment-img-link {
  display: block;
  max-width: 200px;
  border-radius: 4px;
  overflow: hidden;
}
.attachment-img {
  width: 100%;
  height: auto;
  display: block;
}
.attachment-file-link {
  display: inline-block;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  font-size: 12px;
  text-decoration: none;
  color: var(--message-text-color);
}
.attachment-file-link:hover {
  text-decoration: underline;
}

.message_out .message_time {
  color: var(--second-test-color);
}

:deep(.mention) {
 background: rgba(22, 138, 205, 0.15);
 color: var(--accent);
 font-weight: 600;
 padding: 1px 6px;
 border-radius: 10px;
}
.message_out :deep(.mention) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.message_parent {
  border-left: 2px solid var(--accent);
  padding-left: 6px;
  margin-bottom: 6px;
  background: rgba(0,0,0,0.05);
  border-radius: 4px;
  font-size: 12px;
}
.clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}
.clickable:hover {
  opacity: 0.8;
}
.message_out .message_parent {
  border-left: 2px solid #fff;
  background: rgba(255,255,255,0.1);
}
.parent_sender {
  display: block;
  font-weight: bold;
  color: var(--accent);
}
.message_out .parent_sender {
  color: #fff;
}
.parent_text {
  color: var(--text-color);
  opacity: 0.8;
}
.message_out .parent_text {
  color: #fff;
}
.lable{
  font-weight: 500;
}

.messageLeft {
  position: absolute;
  left: -10px;
  bottom: -40px;
  height: 40px;
}

.messageRight {
  position: absolute;
  right: -20px;
  bottom: -30px;
  height: 30px;
  width: 70px;
}
</style>