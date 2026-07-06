// PWA: Service Worker の登録（全ページ共通で読み込む）
(() => {
    if (!('serviceWorker' in navigator)) {
        return;
    }
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => {
            // 登録に失敗してもアプリは通常どおり動作する
        });
    });
})();
