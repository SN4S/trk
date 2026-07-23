<template>
  <div>
    <VitePwaManifest />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>


<script setup lang="ts">
import { watch, onMounted, onUnmounted, nextTick } from 'vue'

const { init, isLoggedIn, currentUser } = useAuth()
const { connect, disconnect } = useWebSocket()
const { addToast } = useToast()
const { subscribeToPush } = usePush()
const router = useRouter()

watch(isLoggedIn, (newVal) => {
    if (newVal) {
        connect()
        subscribeToPush()
    } else {
        disconnect()
    }
}, { immediate: true })
</script>