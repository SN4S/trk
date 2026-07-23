import { joinURL } from 'ufo'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const target = config.apiTarget as string || 'http://localhost:8000'
  
  // Get the path without the /api prefix
  // In a catch-all [...].ts route inside server/api, event.context.params._ contains the rest of the path
  const path = event.context.params?._ || ''
  const query = getQuery(event)
  
  const targetUrl = joinURL(target, path)
  
  return proxyRequest(event, targetUrl)
})
