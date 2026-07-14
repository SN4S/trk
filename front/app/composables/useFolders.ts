/**
 * Folders composable — manages folder CRUD and active folder selection.
 */

export interface ApiFolderGroup {
  id: number
  name: string
}

export interface ApiFolder {
  id: number
  name: string
  groups: ApiFolderGroup[]
}

const foldersStore = reactive({
  folders: [] as ApiFolder[],
  activeFolderId: null as number | null,
  pending: false,
})

export function useFolders() {
  const { apiFetch } = useApi()

  async function fetchFolders() {
    foldersStore.pending = true
    try {
      foldersStore.folders = await apiFetch<ApiFolder[]>('/folders/')
    } catch (e) {
      console.error(e)
    } finally {
      foldersStore.pending = false
    }
  }

  async function createFolder(name: string) {
    const res = await apiFetch<ApiFolder>('/folders/', {
      method: 'POST',
      body: { name }
    })
    foldersStore.folders.push(res)
    return res
  }

  async function deleteFolder(id: number) {
    await apiFetch(`/folders/${id}`, { method: 'DELETE' })
    foldersStore.folders = foldersStore.folders.filter(f => f.id !== id)
    if (foldersStore.activeFolderId === id) {
      foldersStore.activeFolderId = null
    }
  }

  async function addGroupToFolder(folderId: number, groupId: number) {
    await apiFetch(`/folders/${folderId}/groups`, {
      method: 'POST',
      body: { group_id: groupId }
    })
    await fetchFolders() // refresh to get updated groups
  }

  async function removeGroupFromFolder(folderId: number, groupId: number) {
    await apiFetch(`/folders/${folderId}/groups/${groupId}`, {
      method: 'DELETE'
    })
    await fetchFolders()
  }

  function setActiveFolder(id: number | null) {
    if (id === null || foldersStore.activeFolderId === id) {
      foldersStore.activeFolderId = null // toggle off
    } else {
      foldersStore.activeFolderId = id
    }
  }

  return {
    store: foldersStore,
    fetchFolders,
    createFolder,
    deleteFolder,
    addGroupToFolder,
    removeGroupFromFolder,
    setActiveFolder,
  }
}
