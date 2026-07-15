<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>


<script setup lang="ts">
import { watch, onMounted, onUnmounted, nextTick } from 'vue'

const { init, isLoggedIn, currentUser } = useAuth()
const { connect, disconnect, subscribe, unsubscribe } = useWebSocket()
const { addToast } = useToast()
const router = useRouter()

function onNewGeneralMessage(data: any) {
    if (!currentUser.value) return
    if (data.user_id === currentUser.value.id) return

    const isPing = data.message && data.message.includes(`@[${currentUser.value.id}:`)
    const isReply = data.parent && data.parent.user?.id === currentUser.value.id

    if (isPing) {
        addToast({ 
            title: "Нова згадка", 
            message: `Вас згадав ${data.user?.username || 'користувач'} у загальному чаті`, 
            type: 'info',
            onClick: () => router.push(`/general#msg-${data.id}`)
        })
    } else if (isReply) {
        addToast({ 
            title: "Нова відповідь", 
            message: `${data.user?.username || 'Користувач'} відповів на ваше повідомлення`, 
            type: 'info',
            onClick: () => router.push(`/general#msg-${data.id}`)
        })
    }
}

function onNewReply(data: any) {
    if (!currentUser.value) return
    if (data.user_id == currentUser.value.id) return

    if (data.ticket_assigned_to_id == currentUser.value.id) {
        addToast({ 
            title: "Нове повідомлення", 
            message: `Нове повідомлення в тікеті, що призначений вам`, 
            type: 'info',
            onClick: async () => {
                const targetHash = `ticket-${data.ticket_id}`
                // If already on the root page, scroll directly; otherwise navigate then scroll
                if (router.currentRoute.value.path === '/') {
                    await nextTick()
                    const el = document.getElementById(targetHash)
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        el.classList.add('highlight-ticket')
                        setTimeout(() => el.classList.remove('highlight-ticket'), 2000)
                    }
                } else {
                    await router.push(`/#${targetHash}`)
                }
            }
        })
    }
}

onMounted(() => {
    subscribe('new_general_message', onNewGeneralMessage)
    subscribe('new_reply', onNewReply)
})

onUnmounted(() => {
    unsubscribe('new_general_message', onNewGeneralMessage)
    unsubscribe('new_reply', onNewReply)
})

watch(isLoggedIn, (newVal) => {
    if (newVal) {
        connect()
    } else {
        disconnect()
    }
}, { immediate: true })
</script>