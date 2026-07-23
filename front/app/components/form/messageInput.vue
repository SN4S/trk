<template>
  <div class="input_container">
    <!-- Reply Banner -->
    <div v-if="replyingToTicket || replyingToMessage" class="reply_banner">
      <div class="reply_info">
        <template v-if="replyingToMessage">
          <span class="reply_label">Відповідь</span>
          <span class="reply_user">{{ replyingToMessage.sender }}</span>
          <span class="reply_text">{{ replyingToMessage.text }}</span>
        </template>
        <template v-else-if="replyingToTicket">
          <span class="reply_label">Відповідь на тікет: {{replyingToTicket.ticket_num}}</span>
          <span class="reply_user">{{ replyingToTicket.soc_user_name }}</span>
          <span class="reply_text">{{ replyingToTicket.message }}</span>
        </template>
      </div>
      <button class="cancel_reply" @click="emit('cancelReply')" title="Скасувати">✕</button>
    </div>

    <!-- Attachments Preview -->
    <div v-if="attachments.length > 0" class="attachments-preview">
      <div v-for="att in attachments" :key="att.id" class="attachment-item">
        <span class="attachment-name">{{ att.filename }}</span>
        <button class="remove-attachment" @click="removeAttachment(att.id)" title="Видалити">✕</button>
      </div>
    </div>

    <!-- Input Bar -->
    <div class="input_bar">
      <button class="attach-btn" @click="$refs.fileInput.click()" :disabled="isUploading">📎</button>
      <input type="file" ref="fileInput" multiple style="display: none" @change="onFileSelected" />
      <div class="mention-wrap">
      <textarea
        id="message-f" 
        placeholder="Написати..." 
        :value="modelValue"
        @input="onInput"
        @keydown="onKeydown"
        rows="1"
      ></textarea>
        <ul v-if="showMentions" class="mention-list">
          <li v-for="u in filteredUsers" :key="u.id" @mousedown.prevent="pickMention(u.username)">@{{ u.username }}</li>
        </ul>
      </div>
      <button class="send-button" @click="onSend" :disabled="(!modelValue.trim() && !attachments.length && !replyingToTicket && !replyingToMessage) || isUploading">➤</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApiTicket } from '~/composables/useTickets'
const { currentUser } = useAuth()
const { apiFetch } = useApi()
const { addToast } = useToast()

const props = defineProps<{
  modelValue: string
  replyingToTicket?: ApiTicket | null
  replyingToMessage?: { sender: string; text: string } | null
}>()

import { useMentionableUsers } from '~/composables/useMentionableUsers'
const { users: mentionableUsers } = useMentionableUsers()

const attachments = ref<any[]>([])
const isUploading = ref(false)

async function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  isUploading.value = true
  for (let i = 0; i < target.files.length; i++) {
    const file = target.files[i]
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const res = await apiFetch<any>('/attachments/upload', {
        method: 'POST',
        body: formData
      })
      attachments.value.push(res)
    } catch (err: any) {
      addToast({ title: 'Помилка', message: `Не вдалося завантажити ${file.name}`, type: 'error' })
    }
  }
  isUploading.value = false
  target.value = '' // reset input
}

function removeAttachment(id: number) {
  attachments.value = attachments.value.filter(a => a.id !== id)
}

const mentionQuery = computed(() => {
  const m = props.modelValue.match(/@(\w*)$/)
  return m ? m[1] : null
})

const filteredUsers = computed(() => {
  if (mentionQuery.value === null) return []
  const q = mentionQuery.value.toLowerCase()
  return mentionableUsers.value
          .filter(u => u.id !== currentUser.value?.id)
          .filter(u => u.username.toLowerCase().startsWith(q))
          .slice(0, 6)
})

const showMentions = computed(() => mentionQuery.value !== null && filteredUsers.value.length > 0)

function pickMention(username: string) {
  emit('update:modelValue', props.modelValue.replace(/@(\w*)$/, `@${username} `))
}

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'send', attachmentIds: number[]): void
  (e: 'cancelReply'): void
}>()

function onInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = target.scrollHeight + 'px'
  emit('update:modelValue', target.value)
}

function onSend() {
  if (props.modelValue.trim() || attachments.value.length > 0 || props.replyingToTicket || props.replyingToMessage) {
    const ids = attachments.value.map(a => a.id)
    emit('send', ids)
    attachments.value = []

    setTimeout(() => {
      const el = document.getElementById('message-f')
      if (el) el.style.height = 'auto'
    }, 0)
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}
</script>

<style scoped>
.input_container {
  display: flex;
  flex-direction: column;
  background: var(--nav-bar-bg);
  border-top: var(--border);
}

.reply_banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid var(--border);
}

.reply_info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-left: 3px solid var(--accent);
  padding-left: 8px;
}

.reply_label {
  font-size: 11px;
  color: var(--accent);
  font-weight: bold;
}

.reply_user {
  font-size: 12px;
  font-weight: bold;
  color: var(--message-text-color);
}

.reply_text {
  font-size: 12px;
  color: var(--message-time-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cancel_reply {
  background: none;
  border: none;
  color: var(--message-time-color);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}
.cancel_reply:hover {
  color: var(--message-text-color);
}

.attachments-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 16px;
  background: var(--nav-bar-bg);
  border-bottom: 1px solid var(--border);
}

.attachment-item {
  display: flex;
  align-items: center;
  background: rgba(0,0,0,0.05);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
}

.attachment-name {
  margin-right: 8px;
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.remove-attachment {
  background: none;
  border: none;
  color: var(--message-time-color);
  cursor: pointer;
}
.remove-attachment:hover {
  color: red;
}

.attach-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  color: var(--message-time-color);
}
.attach-btn:hover {
  color: var(--message-text-color);
}
.attach-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input_bar {
  display: flex;
  gap: 0.5rem;
  padding: 0.7rem 0.7rem;
  align-items: center;
}

.mention-wrap #message-f {
  width: 100%;
  background: var(--nav-item-bg-hover-color);
  border: none;
  border-radius: 20px;
  padding: 10px 16px;
  color: var(--message-text-color);
  outline: none;
  resize: none;
  min-height: 40px;
  max-height: 150px;
  font-family: inherit;
  line-height: 1.4;
}

.mention-wrap { position: relative; flex: 1; }
.mention-list {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  background: var(--message-bg-color);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 160px;
  max-height: 180px;
  overflow-y: auto;
  z-index: 50;
  padding: 4px 0;
}
.mention-list li { padding: 6px 12px; font-size: 13px; cursor: pointer; }
.mention-list li:hover { background: var(--nav-item-bg-hover-color); }

.input_bar .send-button {
  background: var(--nav-item-bg-active-color);
  border: none;
  color: #fff;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.input_bar .send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>