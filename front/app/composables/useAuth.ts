interface LoginPayload{
    username: string,
    password: string,
}

interface AccessTokenResponse{
    access_token: string,
    token_type: string,
}

interface UserOut{
    id: number,
    username: string,
    is_active: boolean,
    role: string,
}

const accessToken = ref<string | null>(null)
const currentUser = ref<UserOut | null>(null)
let globalRefreshPromise: Promise<boolean> | null = null

export function useAuth(){
    const config = useRuntimeConfig()
    const baseURL = config.public.apiBase as string
    const router = useRouter()

    const isLoggedIn = computed(() => accessToken.value !== null)

    //get token from local storage
    async function init () {
        if (!process.client) return
        const stored = localStorage.getItem('access_token')
        if (stored) {
            accessToken.value = stored
            await fetchMe()
        }
    }


    async function login(payload:LoginPayload): Promise<void> {
        const data = await $fetch<AccessTokenResponse>('/auth/login', {
            baseURL,
            method: 'POST',
            body: payload,
            credentials: 'include'
        })

        accessToken.value = data.access_token
        if (process.client) localStorage.setItem('access_token', data.access_token)

        await fetchMe()

        await router.push('/')
    }

    async function fetchMe(): Promise<void> {
        try {
            currentUser.value = await $fetch<UserOut>('/auth/me',{
                baseURL,
                headers: {Authorization: `Bearer ${accessToken.value}`},
            })
        }catch{
            currentUser.value = null
        }
    }

    async function refresh(): Promise<boolean> {
        if (globalRefreshPromise) {
            return globalRefreshPromise
        }

        globalRefreshPromise = (async () => {
            try {
                const data = await $fetch<AccessTokenResponse>('/auth/refresh', {
                    baseURL,
                    method: 'POST',
                    credentials: 'include'
                })
                accessToken.value = data.access_token
                if (process.client) localStorage.setItem('access_token', data.access_token)
                return true
            } catch {
                return false
            } finally {
                globalRefreshPromise = null
            }
        })()

        return globalRefreshPromise
    }


    async function logout(): Promise<void> {
        try {
            await $fetch('/auth/logout', {
                baseURL,
                method: 'POST',
                credentials: "include"
            })
        }catch {
            //do nothing
        }finally {
            accessToken.value = null
            currentUser.value = null
            if (process.client) localStorage.removeItem('access_token')
            await router.push('/login')
        }
        }
        return {
            isLoggedIn,
            currentUser,
            accessToken,
            init,
            login,
            fetchMe,
            refresh,
            logout,
    }

}
