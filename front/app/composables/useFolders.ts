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

export function useFolders() {
  const foldersStore = useState('folders:store', () => ({
    folders: [] as ApiFolder[],
    activeFolderId: null as number | null,
    pending: false,
  }))

  const { apiFetch } = useApi()

  async function fetchFolders() {
    foldersStore.value.pending = true
    try {
      foldersStore.value.folders = await apiFetch<ApiFolder[]>('/folders/')
    } catch (e) {
      console.error(e)
    } finally {
      foldersStore.value.pending = false
    }
  }

  async function createFolder(name: string) {
    const res = await apiFetch<ApiFolder>('/folders/', {
      method: 'POST',
      body: { name }
    })
    foldersStore.value.folders.push(res)
    return res
  }

  async function deleteFolder(id: number) {
    await apiFetch(`/folders/${id}`, { method: 'DELETE' })
    foldersStore.value.folders = foldersStore.value.folders.filter(f => f.id !== id)
    if (foldersStore.value.activeFolderId === id) {
      foldersStore.value.activeFolderId = null
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
    if (id === null || foldersStore.value.activeFolderId === id) {
      foldersStore.value.activeFolderId = null // toggle off
    } else {
      foldersStore.value.activeFolderId = id
    }
  }

  return {
    store: foldersStore.value,
    fetchFolders,
    createFolder,
    deleteFolder,
    addGroupToFolder,
    removeGroupFromFolder,
    setActiveFolder,
  }
}
