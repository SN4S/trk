<template>
  <div
    class="itemBlock"
    :class="{ isActive: active }"
    @contextmenu.prevent="emit('delete')"
  >
    <div class="titleBlock">
      <span class="title">{{ folder.name }}</span>
    </div>
    <div v-if="unreadCount > 0" class="iconBlock">
      <span class="number">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiFolder } from '~/composables/useFolders'
import { useGroups } from '~/composables/useGroups'

const props = defineProps<{
  folder: ApiFolder
  active: boolean
}>()

const emit = defineEmits<{
  (e: 'delete'): void
}>()

const { groups } = useGroups()

const unreadCount = computed(() => {
  if (!props.folder.groups?.length) return 0
  const idSet = new Set(props.folder.groups.map(g => g.id))
  return groups.value
    .filter(g => idSet.has(g.id))
    .reduce((sum, g) => sum + (g.unread_count || 0), 0)
})
</script>

<style scoped>
.itemBlock {
  position: relative;
  padding: 0.5rem;
  border-radius: var(--radius);
  border: var(--border);
  cursor: pointer;
  transition: all 0.3s ease;
}

.itemBlock:hover {
  transform: scale(0.9, 0.9);
}

.itemBlock.isActive {
  transform: scale(0.9, 0.9);
  background-color: var(--accent);
  color: var(--second-test-color);
  
}

.titleBlock {
  display: flex;
  justify-content: center;
  align-items: center;
}

.title {
  font-weight: 400;
  font-size: 12px;
}

.iconBlock {
  position: absolute;
  top: -10px;
  right: -10px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 20px;
  min-width: 20px;
  border-radius: 50%;
  background: var(--danger);
}

.number {
  padding: 2px;
  font-weight: 600;
  font-size: 10px;
  color: #fff;
}
</style>
