<template>
  <div class="userMng">
  <div class="admin-content">
    <!--START TOPBAR-->
    <div class="bar">
        <div class="bar-left">
          <form-input v-model="searchQuery" placeholder="Search..." />
        </div>

        <div class="panel">
          <form-select
              v-model="roleFilter"
              :options="['support', 'manager', 'admin']"
              placeholder="Усі ролі"
              size="small"
          />
          <form-reset @click="resetFilters" title="Скинути фільтр">
            &#11119
          </form-reset>
            <div @click="creating = true" class="small_icon">
              <img :src=addIcon  />
            </div>
        </div>
    </div>
    <!--END TOPBAR -->
    <!-- Start List -->
    <div class="list_block">
      <list
          alternating
          :loading="listLoading"
          :empty="filteredUsers.length === 0"
          empty-text="Клієнти не знайдені"
      >
        <template #header>
          <list-item text="ID" />
          <list-item text="Username" />
          <list-item text="Status" />
          <list-item text="Role" />
          <list-item text="Дії" />
        </template>
        <template #body>
          <list-container
              v-for="user in filteredUsers"
              :key="user.id"
              class="listLine"
              @click="startEdit(user)"
          >
            <list-item :text="user.id" />
            <list-item :text="user.username" />
            <list-item :text="user.is_active || '—'" />
            <list-item :text="user.role" />
            <list-item>
              <div class="btn_ico">
                <img :src=removeIcon alt="" @click="deleteUser(user.id)">
              </div>
            </list-item>
          </list-container>
        </template>
      </list>
    </div>
    <!-- / List -->
    <!-- START POPUP-->
    <!---CREATE -->
    <form-popup v-model="creating" title="Створити нового користувача" @opened="focusUsernameInput">
      <form-input
          ref="usernameInputRef"
          v-model="form.username"
          class="create-input"
          placeholder="Логін…"
          maxlength="64"
      />
      <form-input
          v-model="form.password"
          class="create-input"
          placeholder="Пароль…"
          maxlength="64"
          type="password"
      />

        <form-select
            v-model="form.role"
            label="Роль"
            required
            :options="[
      { value: 'support', label: 'Підтримка (support)' },
      { value: 'manager', label: 'Менеджер (manager)' },
      { value: 'admin', label: 'Адміністратор (admin)' },
    ]"/>
      <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>
      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      <template #footer="{ close }">
        <button class="create-cancel" @click="close">Скасувати</button>
        <button class="create-confirm" :disabled="pending" @click="handleRegister(close)">
          {{ pending ? 'Реєстрація...' : 'Зареєструвати' }}
        </button>
      </template>
    </form-popup>
    <!--EDIT -->
    <form-popup v-model="editing" title="Редагувати користувача" @opened="focusEditRoleSelect">
      <form-select
          v-model="editForm.is_active"
          label="Статус"
          :options="[
      { value: true, label: 'Активний' },
      { value: false, label: 'Неактивний' },
    ]"
      />

      <form-select
          ref="editRoleSelectRef"
          v-model="editForm.role"
          label="Роль"
          required
          :options="[
      { value: 'support', label: 'Підтримка (support)' },
      { value: 'manager', label: 'Менеджер (manager)' },
      { value: 'admin', label: 'Адміністратор (admin)' },
    ]"
      />
      <form-input
          v-model="editForm.password"
          class="create-input"
          placeholder="Новий пароль (необов'язково)…"
          maxlength="64"
          type="password"
      />
      <div v-if="editErrorMsg" class="error-msg">{{ editErrorMsg }}</div>
      <template #footer="{ close }">
        <button class="create-cancel" @click="cancelEdit(close)">Скасувати</button>
        <button class="create-confirm" :disabled="editPending" @click="handleSaveEdit(close)">
          {{ editPending ? 'Збереження...' : 'Зберегти' }}
        </button>
      </template>
    </form-popup>
    <!--END POPUP-->
  </div>
  </div>
</template>

<script setup lang="ts">
import { useApi } from '~/composables/useApi'
import { useToast } from '~/composables/useToast'
import { ref, computed, onMounted, nextTick } from 'vue'
import FormPopup from "~/components/form/popup/index.vue";
import removeIcon from '~/assets/img/icons/remove.png'
import addIcon from '~/assets/img/icons/plus.png'

const { apiFetch } = useApi()
const { addToast } = useToast()

interface User {
  id: number
  username: string
  is_active: boolean
  role: string
}

const creating = ref(false);

const usernameInputRef = ref<HTMLInputElement | null>(null)

const searchQuery = ref('')
const roleFilter = ref('')

const filteredUsers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return users.value.filter(u => {
    const matchesQuery = !q || u.username.toLowerCase().includes(q)
    const matchesRole = !roleFilter.value || u.role === roleFilter.value
    return matchesQuery && matchesRole
  })
})

function resetFilters() {
  searchQuery.value = ''
  roleFilter.value = ''
}

async function focusUsernameInput() {
  await nextTick()
  usernameInputRef.value?.focus()
}

async function handleRegister(close: () => void) {
  await registerUser()
  if (!errorMsg.value) close()
}

const users = ref<User[]>([])
const loadingUsers = ref(false)

const form = ref({
  username: '',
  password: '',
  role: 'support'
})
const pending = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

async function fetchUsers() {
  loadingUsers.value = true
  try {
    const data = await apiFetch('/auth/users')
    users.value = data
  } catch (e) {
    console.error('Failed to load users', e)
  } finally {
    loadingUsers.value = false
  }
}

onMounted(() => {
  fetchUsers()
})


////USER CREATE
async function registerUser() {
  if (!form.value.username || !form.value.password) return
  pending.value = true
  successMsg.value = ''
  errorMsg.value = ''
  try {
    await apiFetch('/auth/register', {
      method: 'POST',
      body: {
        username: form.value.username,
        password: form.value.password,
        role: form.value.role
      }
    })
    successMsg.value = 'Користувача успішно зареєстровано!'
    form.value.username = ''
    form.value.password = ''
    form.value.role = 'support'
    fetchUsers()
  } catch (e: any) {
    errorMsg.value = e?.data?.detail ?? 'Помилка реєстрації'
  } finally {
    pending.value = false
  }
}


////USER EDIT
const editing = ref(false)
const editRoleSelectRef = ref<HTMLSelectElement | null>(null)
const editingUserId = ref<number | null>(null)
const editForm = ref({ role: '', is_active: true, password: '' })
const editPending = ref(false)
const editErrorMsg = ref('')

async function focusEditRoleSelect() {
  await nextTick()
  editRoleSelectRef.value?.focus()
}

function startEdit(user: User) {
  editingUserId.value = user.id
  editForm.value = { role: user.role, is_active: user.is_active, password: '' }
  editErrorMsg.value = ''
  editing.value = true
}

function cancelEdit(close: () => void) {
  editingUserId.value = null
  close()
}

async function handleSaveEdit(close: () => void) {
  if (editingUserId.value == null) return

  if (editForm.value.password && editForm.value.password.length < 8) {
    editErrorMsg.value = 'Пароль повинен містити не менше 8 символів'
    return
  }

  editPending.value = true
  editErrorMsg.value = ''
  try {
    const payload: any = { role: editForm.value.role, is_active: editForm.value.is_active }
    if (editForm.value.password) {
      payload.password = editForm.value.password
    }
    await apiFetch(`/auth/users/${editingUserId.value}`, {
      method: 'PUT',
      body: payload
    })
    editingUserId.value = null
    await fetchUsers()
    close()
  } catch (e: any) {
    if (e?.response?.status === 422 && e?.data?.detail && Array.isArray(e.data.detail)) {
      editErrorMsg.value = e.data.detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join('\n')
    } else {
      editErrorMsg.value = e?.data?.detail ?? 'Failed to update user'
    }
  } finally {
    editPending.value = false
  }
}


////DELETE USER
async function deleteUser(userId: number) {
  if (!confirm('Ви впевнені, що хочете видалити цього користувача?')) return
  try {
    await apiFetch(`/auth/users/${userId}`, {
      method: 'DELETE'
    })
    fetchUsers()
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка видалення', type: 'error' })
  }
}
</script>

<style scoped>
.bar {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: row;
  background: var(--nav-bar-bg);
  border-radius: var(--radius);
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.1);
  justify-content: space-between;
  padding: 0.5rem;
  border: var(--border);
}

.btn_ico{
  height: 25px;
  width: 25px;
}

.list_block {
  width: 100%;
}

.panel{
  display: flex;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
}

.panel span {
  background-color: var(--accent);
  padding: 0.5rem;
  color: white;
  line-height: 12px;
  border-radius: var(--radius);
}

.admin-content {
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  width: 100%;
  box-sizing: border-box;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  color: var(--message-time-color);
}

.success-msg {
  color: #2e8b57;
  font-size: 13px;
}
.error-msg {
  color: #e05252;
  font-size: 13px;
}
.users-table th, .users-table td {
  padding: 12px;
  text-align: left;
  border-bottom:var(--border);
}
.users-table th {
  color: var(--message-time-color);
  font-weight: 500;
  white-space: nowrap;
}
.users-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}
.actions input{
  width: 40%;
}
.listLine:nth-child(2n + 1) {
  background-color: #f4f3f3;
}
</style>