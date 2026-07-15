<template>
  <div class="filter-strip">
    <!-- Theme select -->
    <div class="filters">
      <form-select
          id="filter-theme"
          :model-value="filter.themeId"
          :options="themes.map(t => ({ value: t.id, label: t.name }))"
          placeholder="Усі теми"
          size="small"
          @update:model-value="v => setTheme(v ? +v : null)"
      />

      <form-select
          id="filter-status"
          :model-value="filter.status"
          :options="STATUSES"
          placeholder="Усі статуси"
          size="small"
          @update:model-value="v => setStatus((v || null) as TicketStatus | null)"
      />


    <!-- My Tickets -->
    <button 
      class="status-pill my-tickets"
      :class="{ active: filter.assignedToMe }"
      @click="setAssignedToMe(!filter.assignedToMe)"
    >
      Мої тікети
    </button>
    </div>
    <!-- Reset -->
    <button class="reset-btn" @click="reset" title="Скинути фільтр">
      &#11119
    </button>
  </div>
</template>

<script setup lang="ts">
import { useFilter } from '~/composables/useFilter'
import { useThemes } from '~/composables/useThemes'

const { filter, setTheme, setStatus, setAssignedToMe, reset } = useFilter()
const { themes, fetchThemes } = useThemes()

const STATUSES = [
  { value: 'open',    label: 'Відкриті' },
  { value: 'pending', label: 'В роботі' },
  { value: 'closed',  label: 'Закриті' },
] as const

const hasActiveFilters = computed(
    () => filter.status !== null || filter.themeId !== null || filter.assignedToMe
)

onMounted(fetchThemes)
</script>

<style scoped>
.filter-strip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 0.5rem;
  background: var(--nav-bar-bg);
  border: var(--border);
  border-radius: var(--radius);
}
.filters {
  display: flex;
  gap: 0.5rem;
  flex-direction: row;
}
.filters > * {
  flex: 1 1 0;
  min-width: 0;
}

.status-pill {
  box-sizing: border-box;
  width: 6rem;
  height: 28px;
  padding: 0 8px;
  font-size: 12px;
  line-height: 26px;
  border-radius: var(--radius);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-pill {
  background: var(--nav-bar-bg);
  color: var(--message-text-color);
  border: none;
  cursor: pointer;
  outline: none;
  transition: box-shadow 0.2s;
}
.status-pill.my-tickets { color: var(--message-text-color); border: var(--border); }
.status-pill.my-tickets.active { background: var(--accent); color: white; }
.status-pill:hover { background: var(--accent); opacity: 0.85; color: white; }

.reset-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  opacity: 0.6;
  transition: opacity 0.2s, color 0.2s;
}
.reset-btn:hover {
  opacity: 1;
  color: #e05252;
}
</style>