<template>
  <div class="message" :class="{'message_out': alignRight}">
    <p class="message_sender">
      {{ displayName }}
    </p>
    <p class="message_text" v-if="!hideText">{{ message.message }}</p>
    <slot name="extra"></slot>
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

</style>