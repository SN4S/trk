<template>
  <div class="status-wrapper" :class="{ interactive }" @click.stop.prevent="togglePopup">
    <span class="ticket_status" :class="status">{{ statusMap[status] || status }}</span>
    <div v-if="showPopup" class="status-popup">
      <div class="status-option open" @click.stop.prevent="selectStatus('open')">відкритий</div>
      <div class="status-option pending" @click.stop.prevent="selectStatus('pending')">в роботі</div>
      <div class="status-option closed" @click.stop.prevent="selectStatus('closed')">закритий</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'

const statusMap: Record<string, string> = {
  open: 'відкритий',
  pending: 'в роботі',
  closed: 'закритий'
}

const props = defineProps({
  status: String,
  interactive: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update'])

const showPopup = ref(false)

function togglePopup() {
  if (!props.interactive) return
  if (showPopup.value) {
    showPopup.value = false
  } else {
    showPopup.value = true
    setTimeout(() => {
      document.addEventListener('click', closePopup)
    }, 0)
  }
}

function closePopup() {
  showPopup.value = false
  document.removeEventListener('click', closePopup)
}

onBeforeUnmount(() => {
  document.removeEventListener('click', closePopup)
})

function selectStatus(newStatus: string) {
  if (newStatus !== props.status) {
    emit('update', newStatus)
  }
  closePopup()
}
</script>

<style scoped>
.status-wrapper {
  position: absolute;
  top: 8px;
  right: 12px;
  z-index: 10;
}

.status-wrapper.interactive {
  cursor: pointer;
}

.ticket_status {
  font-size: 10px;
  text-transform: uppercase;
  font-weight: bold;
  border-radius: 4px;
  padding: 1px 5px;
  display: inline-block;
  user-select: none;
}

.ticket_status.open { background: rgba(224, 82, 82, 0.15); color: #e05252; }
.ticket_status.pending { background: rgba(240, 173, 78, 0.15); color: #f0ad4e; }
.ticket_status.closed { background: rgba(158, 192, 135, 0.15); color: #9ec087; }

.status-popup {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--message-bg-color, #fff);
  border: 1px solid var(--border, #ccc);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 20;
}

.status-option {
  padding: 6px 16px;
  font-size: 10px;
  text-transform: uppercase;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.status-option:hover {
  background: var(--nav-item-bg-hover-color, #f0f0f0);
}

.status-option.open { color: #e05252; }
.status-option.pending { color: #f0ad4e; }
.status-option.closed { color: #9ec087; }
</style>