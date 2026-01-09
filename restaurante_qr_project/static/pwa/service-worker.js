// ========================================
// SGIR - Service Worker para PWA
// Proporciona funcionalidad offline y caché
// ========================================

const CACHE_NAME = 'sgir-cache-v1';
const STATIC_CACHE = 'sgir-static-v1';
const DYNAMIC_CACHE = 'sgir-dynamic-v1';

// Archivos a cachear en la instalación
const STATIC_ASSETS = [
  '/',
  '/login/',
  '/static/css/login.css',
  '/static/js/cliente/formulario.js',
  '/static/images/no-image.svg',
  '/static/pwa/manifest.json',
];

// Instalación del Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando...');
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[Service Worker] Cacheando archivos estáticos');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activando...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== STATIC_CACHE && cache !== DYNAMIC_CACHE) {
            console.log('[Service Worker] Eliminando caché antigua:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Estrategia de caché: Network First con fallback a caché
self.addEventListener('fetch', (event) => {
  // Ignorar peticiones no-GET
  if (event.request.method !== 'GET') {
    return;
  }

  // Ignorar peticiones a APIs (siempre usar red)
  if (event.request.url.includes('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Network First: Intentar red primero, luego caché
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clonar respuesta para guardar en caché
        const responseClone = response.clone();

        // Guardar en caché dinámico
        caches.open(DYNAMIC_CACHE).then((cache) => {
          cache.put(event.request, responseClone);
        });

        return response;
      })
      .catch(() => {
        // Si falla la red, buscar en caché
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }

          // Si no está en caché, retornar página offline genérica
          if (event.request.destination === 'document') {
            return caches.match('/');
          }
        });
      })
  );
});

// Manejo de mensajes desde el cliente
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Sincronización en segundo plano (opcional)
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Sincronizando en segundo plano');
  if (event.tag === 'sync-pedidos') {
    event.waitUntil(syncPedidos());
  }
});

// Función auxiliar para sincronizar pedidos offline
async function syncPedidos() {
  try {
    // Aquí puedes implementar lógica para sincronizar datos offline
    console.log('[Service Worker] Sincronizando pedidos...');
    // const response = await fetch('/api/pedidos/sync/', {method: 'POST'});
    // return response.ok;
  } catch (error) {
    console.error('[Service Worker] Error sincronizando:', error);
  }
}
