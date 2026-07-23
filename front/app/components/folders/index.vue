<template>
  <!-- Start Folders -->
  <div class="foldersBlock">
    <folders-item
        v-for="folder in store.folders"
        :key="folder.id"
        :folder="folder"
        :active="store.activeFolderId === folder.id"
        @click="setActiveFolder(folder.id)"
        @delete="onDelete(folder.id)"
    />
    <button class="add-btn" title="Нова папка" @click="creating = true">+</button>
  </div>
  <!-- / Folders -->
<!-- Start Form -->
  <form-popup v-model="creating" title="Створити нову папку" @opened="focusInput">
    <!-- Start Plus -->
    <input
        ref="inputRef"
        v-model="newFolderName"
        class="create-input"
        placeholder="Назва папки…"
        maxlength="64"
        @keydown.enter="submitCreate"
    />
    <!-- /* Plus -->
    <!-- Start Close -->
    <template #footer="{ close }">
      <button class="create-cancel" @click="close">Скасувати</button>
      <button class="create-confirm" @click="submitCreate">Створити</button>
    </template>
    <!-- / Close -->
  </form-popup>
<!-- / Form -->
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useFolders } from '~/composables/useFolders'
import FormPopup from '~/components/form/popup/index.vue'

const {
  store,
  fetchFolders,
  createFolder,
  deleteFolder,
  setActiveFolder,
} = useFolders()
const { addToast } = useToast()

// ── Create folder ────────────────────────────────────────────────────────────
const newFolderName = ref('')
const creating = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

async function focusInput() {
  await nextTick()
  inputRef.value?.focus()
}

async function submitCreate() {
  const name = newFolderName.value.trim()
  if (!name) {
    creating.value = false
    return
  }

  try {
    await createFolder(name)
    creating.value = false
    newFolderName.value = ''
  } catch (e: any) {
    addToast({ title: 'Помилка', message: e?.data?.detail ?? 'Помилка створення папки', type: 'error' })
  }
}

async function onDelete(folderId: number) {
  if (!confirm('Видалити папку?')) return
  await deleteFolder(folderId)
}

onMounted(fetchFolders)
</script>

<style scoped>
.foldersBlock {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.add-btn {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
  height: 20px;
  width: 20px;
  line-height: 1;
  font-size: 16px;
  color: var(--message-time-color);
  cursor: pointer;
  border-radius: 50%;
  border: 1px dashed var(--message-time-color);
  background: none;
  transition: border-color 0.2s, color 0.2s;
}

.add-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.create-input {
  background: var(--input-field-bg-color);
  color: var(--message-text-color);
  border: 1px solid var(--accent);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 13px;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.create-confirm,
.create-cancel {
  border: none;
  cursor: pointer;
  font-size: 13px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.15s;
}
.create-confirm { 
  color: white;
  background:var(--accent); 
}

.create-confirm:hover { 
  opacity: 0.85;
}

.create-cancel { 
  color: var(--message-text-color); 
  background: none; 
}

.create-cancel:hover { 
  background: var(--danger); 
  }
</style>