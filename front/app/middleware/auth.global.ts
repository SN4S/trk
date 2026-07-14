

//auth middleware

export default defineNuxtRouteMiddleware((to)=>{
    const {isLoggedIn , init} = useAuth()

    init()

    const isPublic = to.path === '/login'

    if (!isLoggedIn.value && !isPublic) {
        return navigateTo('/login')
    }

    if (isLoggedIn.value && isPublic) {
        return navigateTo('/')
    }
})