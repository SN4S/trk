export const usePush = () => {
    const config = useRuntimeConfig()
    const { accessToken } = useAuth()
    const baseURL = useBaseUrl()
    
    function urlBase64ToUint8Array(base64String: string) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    const subscribeToPush = async () => {
        if (!process.client) return;
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push messaging is not supported');
            return;
        }

        try {
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                console.warn('Permission not granted for Notification');
                return;
            }
            
            const registration = await navigator.serviceWorker.ready;
            
            let subscription = await registration.pushManager.getSubscription();
            if (!subscription) {
                const keyData = await $fetch<{public_key: string}>(`${baseURL}/notifications/vapid-public-key`);
                if (!keyData.public_key) {
                    console.warn('Backend did not provide a VAPID public key');
                    return;
                }
                const applicationServerKey = urlBase64ToUint8Array(keyData.public_key);
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                });
            }

            const subJSON = subscription.toJSON();
            
            const token = accessToken.value;
            if (!token) return;

            // Send to backend
            await $fetch(`${baseURL}/notifications/push-subscribe`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`
                },
                body: {
                    endpoint: subJSON.endpoint,
                    keys: subJSON.keys
                }
            })
            console.log('Successfully subscribed to push notifications')
        } catch (e) {
            console.error('Error subscribing to push notifications', e)
        }
    }

    return { subscribeToPush }
}
