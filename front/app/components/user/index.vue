<template>
  <div ref="dropdownRef" class="userWrapper">
    <div class="userContainer" @click="toggleDropdown">
      <div class="userImg">
        <img class="userImg" src="@/assets/img/profile.png" :alt="currentUser?.username" />
      </div>
      <div class="userName">
        <span class="name">{{ currentUser?.username }}</span>
      </div>
    </div>

    <div v-if="isOpen" class="dropdown-menu">
      <ul>
        <li><NuxtLink v-if="currentUser?.role === 'admin'" to="/admin">Адмін панель</NuxtLink></li>
        <li><span @click="logout" class="logout-btn">Вийти</span></li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
const { logout, currentUser } = useAuth()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.userWrapper {
  position: relative;
}

.userContainer {
  border: var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: row;
  padding: 0.5rem;
  gap: 0.5rem;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.userImg {
  height: 35px;
  border-radius: var(--radius);
}

.userName {
  font-weight: 500;
}

.dropdown-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 20;
  background-color: var(--nav-bar-bg);
  border: var(--border);
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  min-width: 180px;
  overflow: hidden;
}

.dropdown-menu ul {
  padding: 4px;
  display: flex;
  flex-direction: column;
}

.dropdown-menu li {
  display: flex;
}

.dropdown-menu a,
.dropdown-menu .logout-btn {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0.5rem 1rem;
  border-radius: calc(var(--radius) - 2px);
  font-size: 14px;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.dropdown-menu a:hover,
.dropdown-menu .logout-btn:hover {
  background: var(--nav-item-bg-hover-color);
}

.logout-btn {
  font-weight: bold;
  color: #e05252;
}
</style>