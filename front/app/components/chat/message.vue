<template>
  <div class="message" :class="{'message_out': alignRight}">
    <p class="message_sender">
      {{ displayName }}
    </p>
    <slot name="extra"></slot>
    <p class="message_text" v-if="!hideText" v-html="renderedText"></p>
    <span class="message_time">{{ formattedTime }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiReply } from '~/composables/useReplies'

const props = defineProps<{
  message: ApiReply
  isMe?: boolean | null
  senderName?: string
  hideText?: boolean
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
  return d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
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
</script>

<style scoped>
.message {
  min-width: 80px;
  max-width: 60%;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--message-bg-color);
  align-self: flex-start;

  display: flex;
  flex-direction: column;
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
}

.message_out {
  align-self: flex-end;
  background: var(--nav-item-bg-active-color);
  color: #fff;
}

.message_time {
  display: block;
  font-size: 11px;
  color: var(--message-time-color);
  margin-top: 4px;
  align-self: flex-end;
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
</style>