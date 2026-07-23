import { useAuth } from "~/composables/useAuth";

export function useApi() {
    const baseURL = useBaseUrl()
    const { accessToken, refresh, logout } = useAuth()

    async function apiFetch<T>(path: string, options: Parameters<typeof $fetch>[1] = {}): Promise<T> {
        const fetchOptions = {
            baseURL,
            ...options,
            headers: {
                ...(accessToken.value ? { Authorization: `Bearer ${accessToken.value}` } : {}),
                ...(options.headers ?? {})
            }
        }

        try {
            return await $fetch<T>(path, fetchOptions)
        } catch (error: any) {
            const status = error?.response?.status || error?.statusCode || error?.status;
            
            // Check for 401 Unauthorized
            if (status === 401) {
                // Don't intercept if the refresh itself failed or login failed
                if (path === '/auth/refresh' || path === '/auth/login') {
                    throw error
                }

                // Attempt to refresh the token
                const refreshed = await refresh()

                if (refreshed && accessToken.value) {
                    // Retry original request with the new token
                    fetchOptions.headers = {
                        ...fetchOptions.headers,
                        Authorization: `Bearer ${accessToken.value}`
                    }
                    return await $fetch<T>(path, fetchOptions)
                } else {
                    // Refresh failed (e.g. refresh token expired), log out the user
                    await logout()
                    throw error
                }
            }
            throw error
        }
    }

    return { apiFetch }
}
