export function useBaseUrl() {
    const config = useRuntimeConfig()
    
    if (process.server) {
        return config.apiTarget as string || 'http://api:8000'
    }
    
    if (config.public.apiBase && config.public.apiBase !== '') {
        return config.public.apiBase as string
    }
    
    return `${window.location.protocol}//${window.location.host}`
}
