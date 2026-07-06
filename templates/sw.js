/*
 * Service Worker（PWA用）
 *
 * - 静的ファイル（/static/）: キャッシュ優先。ファイル名にコンテンツハッシュが
 *   付与されるため、キャッシュが古くなる心配はない。
 * - ページ遷移: ネットワーク優先。オフライン時のみ /offline/ を表示する。
 *   ページ自体はキャッシュしないため、常に最新の内容が表示される。
 *
 * 注意: ルートスコープ（/sw.js）で配信する必要があるため、
 * src/ts のビルド成果物ではなくテンプレートとして配信している。
 */
var CACHE_NAME = 'lm-cache-v1';
var OFFLINE_URL = '/offline/';

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.add(OFFLINE_URL);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (key) { return key !== CACHE_NAME; })
            .map(function (key) { return caches.delete(key); })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') {
    return;
  }

  // ページ遷移: ネットワーク優先、オフライン時はフォールバックページ
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(function () {
        return caches.match(OFFLINE_URL);
      })
    );
    return;
  }

  // 静的ファイル: キャッシュ優先（ハッシュ付きファイル名のため安全）
  var url = new URL(request.url);
  if (url.origin === self.location.origin && url.pathname.indexOf('/static/') === 0) {
    event.respondWith(
      caches.match(request).then(function (cached) {
        if (cached) {
          return cached;
        }
        return fetch(request).then(function (response) {
          if (response.ok) {
            var copy = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(request, copy);
            });
          }
          return response;
        });
      })
    );
  }
});
