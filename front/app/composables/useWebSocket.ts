import { useAuth } from './useAuth'

type WebSocketEventCallback = (data: any) => void
const listeners: Record<string, WebSocketEventCallback[]> = {}

let ws: WebSocket | null = null
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null

export function useWebSocket() {
    const { accessToken, isLoggedIn } = useAuth()
    const config = useRuntimeConfig()

    function connect() {
        if (!process.client) return
        if (ws) return // already connected or connecting
        if (!accessToken.value) return // need auth

        const baseURL = useBaseUrl()
        
        let wsURL = ''
        if (baseURL.startsWith('http')) {
            wsURL = baseURL.replace(/^http/, 'ws') + '/ws/updates?token=' + accessToken.value
        } else {
            // fallback if it somehow is relative
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            wsURL = `${protocol}//${window.location.host}${baseURL}/ws/updates?token=${accessToken.value}`
        }

        ws = new WebSocket(wsURL)

        ws.onopen = () => {
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout)
                reconnectTimeout = null
            }
        }

        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data)
                const type = payload.type
                const data = payload.data

                if (type === 'notification_event') {
                    if (listeners['notification']) {
                        listeners['notification'].forEach(cb => cb(data))
                    }
                    return
                }

                if (listeners[type]) {
                    listeners[type].forEach(cb => cb(data))
                }
            } catch (e) {
                console.error("WS parse error", e)
            }
        }

        ws.onclose = () => {
            ws = null
            // Reconnect if still logged in
            if (isLoggedIn.value) {
                reconnectTimeout = setTimeout(connect, 3000)
            }
        }

        ws.onerror = (error) => {
            console.error("WebSocket error", error)
        }
    }

    function disconnect() {
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout)
            reconnectTimeout = null
        }
        if (ws) {
            ws.close()
            ws = null
        }
    }

    function subscribe(type: string, callback: WebSocketEventCallback) {
        if (!listeners[type]) {
            listeners[type] = []
        }
        // Deduplicate — don't add same callback twice
        if (!listeners[type].includes(callback)) {
            listeners[type].push(callback)
        }
    }

    function unsubscribe(type: string, callback: WebSocketEventCallback) {
        if (listeners[type]) {
            listeners[type] = listeners[type].filter(cb => cb !== callback)
        }
    }

    return { connect, disconnect, subscribe, unsubscribe }
}
