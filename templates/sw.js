/*
 * Service Worker（PWA用）
 *
 * - 静的ファイル: HTTPキャッシュへ委ねる。SWには世代ごとの資産を蓄積しない。
 * - ページ遷移: ネットワーク優先。オフライン時のみ /offline/ を表示する。
 *   ページ自体はキャッシュしないため、常に最新の内容が表示される。
 *
 * 注意: ルートスコープ（/sw.js）で配信する必要があるため、
 * src/ts のビルド成果物ではなくテンプレートとして配信している。
 */
var CACHE_NAME = 'lm-offline-v2';
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
        keys.filter(function (key) { return /^lm-(cache|offline)-/.test(key) && key !== CACHE_NAME; })
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
        return caches.open(CACHE_NAME).then(function (cache) { return cache.match(OFFLINE_URL); });
      })
    );
    return;
  }

  // /static/ はハッシュ付きURLとHTTP Cache-Controlで更新・再利用する。
});
