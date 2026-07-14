<template>
  <div class="input_container">
    <!-- Reply Banner -->
    <div v-if="replyingToTicket" class="reply_banner">
      <div class="reply_info">
        <span class="reply_label">Відповідь на тікет: {{replyingToTicket.ticket_num}}</span>
        <span class="reply_user">{{ replyingToTicket.soc_user_name }}</span>
        <span class="reply_text">{{ replyingToTicket.message }}</span>
      </div>
      <button class="cancel_reply" @click="emit('cancelReply')" title="Скасувати">✕</button>
    </div>

    <!-- Input Bar -->
    <div class="input_bar">
      <input 
        id="message-f" 
        placeholder="Написати..." 
        :value="modelValue"
        @input="onInput"
        @keydown="onKeydown"
      />
      <div v-if="!hideCheckbox" class="checkbox-wrapper" title="Необхідна відповідь від клієнта">
        <input 
          id="check" 
          type="checkbox" 
          :checked="requiresClientReply"
          @change="emit('update:requiresClientReply', ($event.target as HTMLInputElement).checked)"
        />
        <label for="check">❓</label>
      </div>
      <button @click="onSend" :disabled="!modelValue.trim() && !replyingToTicket">➤</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApiTicket } from '~/composables/useTickets'

const props = defineProps<{
  modelValue: string
  replyingToTicket?: ApiTicket | null
  requiresClientReply?: boolean
  hideCheckbox?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'update:requiresClientReply', val: boolean): void
  (e: 'send'): void
  (e: 'cancelReply'): void
}>()

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}

function onSend() {
  if (props.modelValue.trim() || props.replyingToTicket) {
    emit('send')
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

.input_bar {
  display: flex;
  gap: 0.5rem;
  padding: 0.7rem 0.7rem;
  align-items: center;
}

.input_bar #message-f {
  flex: 1;
  background: var(--nav-item-bg-hover-color);
  border: none;
  border-radius: 20px;
  padding: 10px 16px;
  color: var(--message-text-color);
  outline: none;
}

.input_bar #check {
  width: 24px;
  height: 24px;
  cursor: pointer;
}

.input_bar button {
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
.input_bar button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 32px;
  height: 32px;
}
.checkbox-wrapper input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
  z-index: 2;
}
.checkbox-wrapper label {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--nav-item-bg-hover-color);
  border-radius: 8px;
  font-size: 16px;
  transition: background 0.2s;
  cursor: pointer;
}
.checkbox-wrapper input[type="checkbox"]:checked + label {
  background: var(--accent);
  color: #fff;
}
</style>