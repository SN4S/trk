// auth middleware
export default defineNuxtRouteMiddleware(async (to) => {
        if (process.server) return // let SSR pass through, client will restore + redirect if needed

    const { isLoggedIn, init } = useAuth()
    await init()

    const isPublic = to.path === '/login'
    if (!isLoggedIn.value && !isPublic) return navigateTo('/login')
    if (isLoggedIn.value && isPublic) return navigateTo('/')
})