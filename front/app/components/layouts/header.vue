<template>
  <div class="header">
    <!-- Start Group Folders -->
    <div class="folders_block">
      <folders />
    </div>
    <!-- / Group Folders -->
    <div class="rightHeader">
    <!-- Start Filter Strip -->
    <chat-filter />
    <!-- / END Filter Strip -->
    <!-- Start Dashboard -->
    <div class="dashboard_block">
      <dashboard-ticket title="Загальна кількість" :data="stats?.all ?? 0" color="red" />
      <dashboard-ticket title="Не опрацьовані" :data="stats?.open ?? 0" color="blue" />
      <dashboard-ticket title="В роботі" :data="stats?.pending ?? 0" color="green" />
      <dashboard-ticket title="Завершені" :data="stats?.closed ?? 0" color="#9ec087" />
    </div>
    <!-- / Dashboard -->
    <user/>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuth } from "~/composables/useAuth"

const { logout, currentUser } = useAuth()
const route = useRoute()

const groupId = computed(() => {
  const parsed = parseInt(route.params.id as string, 10)
  return isNaN(parsed) ? null : parsed
})

const { stats } = useTicketStats(groupId)
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  height: 57px;
  border-bottom: var(--border);
  background-color: var(--message-bg-color);
}

.dashboard_block {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

.folders_block {
  width: 30%;
}

.rightHeader {
  display: flex;
  flex-direction: row;
  justify-content: end;
  align-items: center;
  width: 70%;
  gap: 0.5rem;
}
</style>
