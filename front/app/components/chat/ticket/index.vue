<template>
  <div class="ticket">
    <chat-ticket-status :status="ticket.status" :interactive="true" @update="changeStatus" />
    <p class="ticket_sender">{{ticket.soc_user_name}}</p>
    <p><span class="lable">Тема:</span> {{ ticket.theme?.name }}</p>
    <p class="ticket_number"><span class="lable">Номер звернення:</span> {{ticket.ticket_num}}</p>
    <p class="ticket_upd_date"><span class="lable">Востаннє оновлено:</span> {{ formattedTimeUpd }}</p>
    <p v-if="ticket.current_assignment?.assigned_to" class="ticket_assigned">
      <span class="lable">Призначено:</span>
      {{ ticket.current_assignment.assigned_to.username }}
      <span class="ticket_assigned_by"> (ким: {{ ticket.current_assignment.assigned_by.username }})</span>
    </p>
    <p class="ticket_text"><span class="lable">Повідомлення:</span> {{ ticket.message }}</p>

    <div v-if="ticket.attachments && ticket.attachments.length > 0" class="attachments-list">
      <template v-for="att in ticket.attachments" :key="att.id">
        <a v-if="att.content_type.startsWith('image/')" :href="baseURL + att.file_url" target="_blank" class="attachment-img-link">
          <img :src="baseURL + att.file_url" :alt="att.filename" class="attachment-img" />
        </a>
        <a v-else :href="baseURL + att.file_url" target="_blank" class="attachment-file-link">
          📎 {{ att.filename }}
        </a>
      </template>
    </div>

    <span class="ticket_date">{{ formattedTimeCr }}</span>
    <div class="controls msg-controls">
      <slot name="controls">

      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiTicket } from '~/composables/useTickets'
const baseURL = useRuntimeConfig().public.apiBase as string

const props = defineProps<{
  ticket: ApiTicket
}>()

const formattedTimeCr = computed(() => {
  const s = props.ticket.created_at
  const d = new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z')
  const now = new Date()
  const isToday = d.getDate() === now.getDate() && 
                  d.getMonth() === now.getMonth() && 
                  d.getFullYear() === now.getFullYear()
  const timeStr = d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
  if (isToday) return timeStr
  return `${d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit', year: '2-digit' })} ${timeStr}`
})
const formattedTimeUpd = computed(() => {
  if (!props.ticket.updated_at) return '—'
  const s = props.ticket.updated_at
  const d = new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z')
  const now = new Date()
  const isToday = d.getDate() === now.getDate() && 
                  d.getMonth() === now.getMonth() && 
                  d.getFullYear() === now.getFullYear()
  const timeStr = d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
  if (isToday) return timeStr
  return `${d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit', year: '2-digit' })} ${timeStr}`
})

import { useApi } from '~/composables/useApi'
const { apiFetch } = useApi()
const { addToast } = useToast()

async function changeStatus(newStatus: string) {
  try {
    await apiFetch(`/tickets/${props.ticket.id}`, {
      method: 'PATCH',
      body: { status: newStatus }
    })
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка оновлення статусу', type: 'error' })
  }
}
</script>

<style scoped>
.ticket {
  position: relative;
  min-width: 180px;
  max-width: 60%;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--message-bg-color);
  align-self: flex-start;

  display: flex;
  flex-direction: column;
}

.ticket_sender{
  color: var(--accent);
  margin-bottom: 4px ;
  font-weight: bold;
  padding-right: 60px;
}

.ticket_text {
  margin: 8px 0 0;
  word-break: break-word;
  white-space: pre-wrap;
}

.ticket_date {
  display: block;
  font-size: 11px;
  color: var(--message-time-color);
  user-select: none;
  margin-top: 4px;
  align-self: flex-end;
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

.lable{
  font-weight: 500;
}
.ticket_assigned_by {
  font-size: 11px;
  opacity: 0.6;
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

</style>