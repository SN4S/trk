<template>
  <div class="chat_block">
    <div class="messageArea">
      <div v-if="pending" class="state-msg">Завантаження…</div>
      <div v-else-if="error" class="state-msg error">{{ error }}</div>
      <div v-else-if="mappedMessages.length === 0" class="state-msg muted">Повідомлень немає</div>
      
      <chat-message 
        v-else 
        v-for="msg in mappedMessages" 
        :key="msg.id" 
        :message="msg"
        :is-me="msg.is_support"
        :sender-name="msg.user?.username || 'Support'"
        :hide-text="!!msg.ticket"
      >
        <template #extra v-if="msg.ticket">
          <div class="forwarded-card">
            <div class="card-header">
              <span class="icon">🎫</span>
              <span class="title">Переслано тікет #{{ msg.ticket.ticket_num }}</span>
              <span class="status-badge" :class="msg.ticket.status?.toLowerCase()">{{ msg.ticket.status }}</span>
            </div>
            
            <div class="card-body">
              <div class="info-row">
                <strong>Група:</strong> {{ msg.ticket.group?.name || 'Невідома група' }}
              </div>
              <div class="info-row">
                <strong>Тема:</strong> {{ msg.ticket.theme?.name || 'Невідома тема' }}
              </div>
              <div class="info-row">
                <strong>Від:</strong> @{{ msg.ticket.soc_user_name }}
              </div>
              
              <div class="message-excerpt" v-if="msg.ticket.message">
                "{{ msg.ticket.message.length > 100 ? msg.ticket.message.substring(0, 100) + '...' : msg.ticket.message }}"
              </div>
            </div>
            
            <div class="card-actions">
              <NuxtLink :to="`/group/${msg.ticket.group_id}#ticket-${msg.ticket_id}`" class="action-btn">
                Перейти до тікету
              </NuxtLink>
            </div>
          </div>
        </template>
      </chat-message>
    </div>


    <!-- Message Input -->
    <div class="input-area">
      <message-input 
        v-model="messageText"
        hide-checkbox
        @send="sendMessage"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useApi } from '~/composables/useApi'
import { useAuth } from '~/composables/useAuth'
import { useFilter } from '~/composables/useFilter'
import MessageInput from '~/components/form/messageInput.vue'
import ChatMessage from '~/components/chat/message.vue'

const { apiFetch } = useApi()
const { currentUser } = useAuth()

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
    ticket: msg.ticket
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

async function sendMessage() {
  if (!messageText.value.trim()) return
  
  try {
    await apiFetch('/general-chat/messages', {
      method: 'POST',
      body: {
        message: messageText.value
      }
    })
    messageText.value = ''
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
.state-msg {
  text-align: center;
  padding: 20px;
  color: var(--message-time-color);
}
.state-msg.error { color: #e05252; }
.forwarded-card {
  margin-top: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  border-left: 3px solid rgba(0, 0, 0, 0.2);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: var(--message-text-color);
}
.message_out .forwarded-card {
  background: rgba(255, 255, 255, 0.05);
  border-left-color: rgba(255, 255, 255, 0.3);
  color: #fff;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
}
.status-badge {
  margin-left: auto;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  background: rgba(0,0,0,0.1);
  color: inherit;
}
.message_out .status-badge {
  background: rgba(255,255,255,0.15);
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-row {
  opacity: 0.8;
}
.message-excerpt {
  margin-top: 4px;
  font-style: italic;
  opacity: 0.7;
  padding-left: 8px;
  border-left: 2px solid rgba(0, 0, 0, 0.15);
}
.message_out .message-excerpt {
  border-left-color: rgba(255, 255, 255, 0.2);
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
  padding: 6px 12px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
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
</style>
