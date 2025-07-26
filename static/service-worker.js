// Install event: cache static assets
self.addEventListener("install", (event) => {
  console.log("📦 Service Worker installing...");

  event.waitUntil(
    caches.open("smartguard-cache").then((cache) => {
      return cache.addAll([
        "/",                         // root
        "/static/style.css",         // styles
        "/static/script.js",         // main JS
        "/static/icons/icon-192.png",
        "/static/icons/icon-512.png"
      ]);
    })
  );

  self.skipWaiting(); // Activate new service worker immediately
});

// Activate event
self.addEventListener("activate", (event) => {
  console.log("✅ Service Worker activated");
});

// Fetch event: respond with cache first, fallback to network
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request);
    })
  );
});
