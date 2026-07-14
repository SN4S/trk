<template>
  <NuxtLink :to="isGlobal ? '/general' : `/group/${group?.id}`" :class="{ 'is-active': isActive }" @contextmenu.prevent="emit('contextmenu', $event)">
    <div class="group-container" :class="{ 'is-active': isActive }">
      <div class="image">
        <img :src="isGlobal ? earthIcon : profileIcon " alt="Group Avatar">
      </div>
      <div class="info">
        <div class="top_row">
          <div class="group-title">{{ isGlobal ? 'Головний чат' : group?.name }}</div>
        </div>
        <div class="last-message muted">
          {{ isGlobal ? 'General group' : (group?.tg_group_id ? `TG: ${group.tg_group_id}` : 'Telegram group') }}
        </div>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import earthIcon from '@/assets/img/earth.webp'
import profileIcon from '@/assets/img/profile.png'
import { computed } from 'vue'
import type { ApiGroup } from '~/composables/useGroups'

const route = useRoute()

const props = defineProps<{
  isGlobal?: boolean
  group?: ApiGroup
}>()

const emit = defineEmits<{
  contextmenu: [event: MouseEvent]
}>()

const isActive = computed(() =>
    props.isGlobal ? route.path.startsWith('/general') : route.path === `/group/${props.group?.id}`
)
</script>

<style scoped>
.group-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 10px 12px;
  border-bottom: var(--border);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.group-container:hover {
  background-color: var(--nav-item-bg-hover-color);
}

.group-container:enabled {
  background-color: var(--nav-item-bg-active-color);
}

.image img {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.info {
  display: flex;
  flex-direction: column;
  flex: 1;
  justify-content: center;
  min-width: 0;
}

.group-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--message-text-color);
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top_row{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-direction: row;
}

.last_sender{
  font-size: 14px;
  font-weight: bold;
  color: var(--accent);
}

.last-message {
  font-size: 14px;
  color: var(--message-time-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


.last_msg_date{
  color: var(--message-time-color);
  justify-content: end;
}

.group-container.is-active {
  background-color: var(--nav-item-bg-active-color);
}


.group-container.is-active .group-title,
.group-container.is-active .last-message,
.group-container.is-active .last_msg_date,
.group-container.is-active .last_sender {
  color: var(--second-test-color);
}


</style>