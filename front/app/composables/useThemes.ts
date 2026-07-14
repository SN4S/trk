/**
 * Themes composable — fetches all available themes from the API
 * and exposes them for use in the filter dropdown.
 */

export interface Theme {
    id: number
    name: string
}

export function useThemes() {
    const { apiFetch } = useApi()

    const themes = ref<Theme[]>([])
    const pending = ref(false)
    const error = ref<string | null>(null)

    async function fetchThemes() {
        pending.value = true
        error.value = null
        try {
            themes.value = await apiFetch<Theme[]>('/themes/')
        } catch (e: any) {
            error.value = e?.data?.detail ?? 'Failed to load themes'
        } finally {
            pending.value = false
        }
    }

    return { themes, pending, error, fetchThemes }
}