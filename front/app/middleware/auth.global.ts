// auth middleware
export default defineNuxtRouteMiddleware(async (to) => {
    const { isLoggedIn, init } = useAuth()

    // Await init so the refresh-cookie restore completes before route guard runs
    await init()

    const isPublic = to.path === '/login'

    if (!isLoggedIn.value && !isPublic) {
        return navigateTo('/login')
    }

    if (isLoggedIn.value && isPublic) {
        return navigateTo('/')
    }
})