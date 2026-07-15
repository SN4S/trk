<template>
  <div class="sidebar">
    <!--SIDEBAR HEADER START-->
    <div class="sidebar-header">
      <SidebarLogo />
      <sidebar-search/>
    </div>
    <!--SIDEBAR HEADER END-->

    <!--GROUP LIST START-->
    <div class="list" @click="closeMenu">
      <sidebar-group :isGlobal="true" :group="generalGroupObj" />
      <!-- Loading -->
      <div v-if="pending" class="state-row">Завантаження…</div>

      <!-- Error -->
      <div v-else-if="error" class="state-row error">{{ error }}</div>

      <!-- Groups -->
      <template v-else>
        <template v-if="visibleGroups.length > 0">
          <sidebar-group
              v-for="group in visibleGroups"
              :key="group.id"
              :group="group"
              @contextmenu="openGroupMenu($event, group)"
          />
        </template>
        <div v-else class="state-row muted">Нічого не знайдено</div>
      </template>
    </div>
    <!--GROUP LIST END-->

    <!-- Context Menu for "Add to folder" -->
    <div 
      v-if="menu.show" 
      class="ctx-menu" 
      :style="{ top: menu.y + 'px', left: menu.x + 'px' }"
      @click.stop
    >
      <div v-if="store.activeFolderId" class="ctx-section">
        <button 
          class="ctx-item danger"
          @click="removeFromFolder(store.activeFolderId, menu.group!.id)"
        >
          ✕ Видалити з папки
        </button>
        <div class="ctx-divider"></div>
      </div>

      <div class="ctx-header">Додати в папку:</div>
      <div v-if="store.folders.length === 0" class="ctx-item muted">Немає папок</div>
      <button 
        v-for="folder in store.folders" 
        :key="folder.id" 
        class="ctx-item"
        @click="addToFolder(folder.id, menu.group!.id)"
      >
        {{ folder.name }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import SidebarGroup from "~/components/sidebar/group.vue"
import { useGroups, type ApiGroup } from "~/composables/useGroups"
import { useFolders } from "~/composables/useFolders"
import { useAuth } from "~/composables/useAuth"
import { useApi } from "~/composables/useApi"
import { useWebSocket } from "~/composables/useWebSocket"

const { currentUser } = useAuth()
const { groups: allGroups, pending, error, fetchGroups } = useGroups()
const { store, addGroupToFolder, removeGroupFromFolder } = useFolders()
const { apiFetch } = useApi()

// ── General Chat Last Message ────────────────────────────────────────────────
const generalLastMessage = ref<string | null>(null)
const generalLastTime = ref<Date | null>(null)
const generalGroupObj = computed(() => ({ 
  last_message: generalLastMessage.value,
  last_time: generalLastTime.value 
} as any))

async function fetchGeneralLatest() {
  try {
    const messages = await apiFetch<any[]>('/general-chat/messages')
    if (messages && messages.length > 0) {
      const last = messages[messages.length - 1]
      const author = last.user?.username || 'Support'
      generalLastMessage.value = `${author}: ${last.message}`
      generalLastTime.value = new Date(last.created_at)
    }
  } catch(e) {}
}

const { subscribe, unsubscribe } = useWebSocket()

function onNewGeneralMsg(data: any) {
  const author = data.user?.username || 'Support'
  generalLastMessage.value = `${author}: ${data.message}`
  generalLastTime.value = new Date(data.created_at)
}

function onNewReply(data: any) {
  const groupId = data.group_id
  if (!groupId) return
  const group = allGroups.value.find(g => g.id === groupId)
  if (group) {
    // Support reply has user.username; client reply falls back to soc_user_name from the ticket
    const author = data.user?.username || data.soc_user_name || 'Клієнт'
    group.last_message = `${author}: ${data.message}`
    group.last_time = new Date(data.created_at)
  }
}

function onNewTicket(data: any) {
  // Patch the affected group's last_message
  const groupId = data.group_id
  if (!groupId) return
  const group = allGroups.value.find(g => g.id === groupId)
  if (group) {
    const author = data.soc_user_name || 'Клієнт'
    group.last_message = `${author}: ${data.message || ''}`
    group.last_time = new Date(data.created_at)
  }
}

onMounted(() => {
  fetchGeneralLatest()
  subscribe('new_general_message', onNewGeneralMsg)
  subscribe('new_reply', onNewReply)
  subscribe('new_ticket', onNewTicket)
})

onUnmounted(() => {
  unsubscribe('new_general_message', onNewGeneralMsg)
  unsubscribe('new_reply', onNewReply)
  unsubscribe('new_ticket', onNewTicket)
})

// ── Filter groups by active folder ──────────────────────────────────────────
const visibleGroups = computed(() => {
  const activeId = store.activeFolderId
  if (activeId !== null) {
    const folder = store.folders.find(f => f.id === activeId)
    if (folder) {
      const idSet = new Set(folder.groups.map(g => g.id))
      return allGroups.value.filter(g => idSet.has(g.id))
    }
  }
  return allGroups.value
})

// ── Context Menu ─────────────────────────────────────────────────────────────
const menu = ref({
  show: false,
  x: 0,
  y: 0,
  group: null as ApiGroup | null
})

function openGroupMenu(e: MouseEvent, group: ApiGroup) {
  menu.value = {
    show: true,
    x: e.clientX,
    y: e.clientY,
    group
  }
  // Optional: Add click listener to close menu when clicking outside
  document.addEventListener('click', closeMenu, { once: true })
}

function closeMenu() {
  menu.value.show = false
}

async function addToFolder(folderId: number, groupId: number) {
  try {
    await addGroupToFolder(folderId, groupId)
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Помилка додавання до папки')
  } finally {
    closeMenu()
  }
}

async function removeFromFolder(folderId: number, groupId: number) {
  try {
    await removeGroupFromFolder(folderId, groupId)
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Помилка видалення з папки')
  } finally {
    closeMenu()
  }
}
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background-color: var(--nav-bar-bg);
  position: relative;
}
.sidebar-header {
  display: flex;
  flex-direction: row;
  justify-content: center;
  width: 100%;
  align-items: center;
  box-sizing: border-box;
  border-bottom: var(--border);
  padding: 0.52rem;
  gap: 12px;
}
.list{
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
}

.state-row {
  padding: 20px 16px;
  text-align: center;
  font-size: 13px;
  color: var(--message-time-color);
}
.state-row.error { color: #e05252; }
.state-row.muted { opacity: 0.6; }
.logout-btn {
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--message-time-color);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: background 0.15s, color 0.15s;
  line-height: 1;
}
.logout-btn:hover {
  background: rgba(224, 82, 82, 0.12);
  color: #e05252;
}

/* Context Menu */
.ctx-menu {
  position: fixed;
  background: var(--message-bg-color);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 0;
  min-width: 160px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 9999;
}
.ctx-header {
  padding: 4px 12px 6px;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--message-time-color);
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}
.ctx-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 6px 12px;
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
.ctx-item.muted {
  color: var(--message-time-color);
  cursor: default;
}
.ctx-item.muted:hover {
  background: none;
}
.ctx-item.danger {
  color: #e05252;
}
.ctx-item.danger:hover {
  background: rgba(224, 82, 82, 0.12);
}
.ctx-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}
</style>