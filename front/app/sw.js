import { precacheAndRoute } from 'workbox-precaching'

precacheAndRoute(self.__WB_MANIFEST || [])

self.addEventListener('push', function(event) {
  if (event.data) {
    let data = {};
    try {
        data = event.data.json();
    } catch (e) {
        data = { body: event.data.text() };
    }
    const title = data.title || 'XPro Support';
    const options = {
      body: data.body || 'You have a new update.',
      icon: '/pwa-192x192.svg',
      badge: '/pwa-192x192.svg',
      data: data
    };

    event.waitUntil(self.registration.showNotification(title, options));
  }
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const data = event.notification.data || {};
  const url = data.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      // Look for an already-open PWA window within our scope
      for (const client of clientList) {
        if (client.url.startsWith(self.registration.scope)) {
          // Found a PWA window — navigate it to the target URL and focus it
          if ('navigate' in client) {
            client.navigate(url);
          }
          return client.focus();
        }
      }
      // No PWA window open — openWindow() resolves to the installed PWA app
      return clients.openWindow(url);
    })
  );
});
