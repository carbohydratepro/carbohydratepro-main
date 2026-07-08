// 画面遷移時のスケルトンスクリーン（全ページ共通で読み込む）
// ページ遷移を伴うクリック・フォーム送信を検知した瞬間にコンテンツ領域を
// スケルトンで覆い、次のページが届くまで白画面の代わりに表示する。
(() => {
    // 遷移が発生しなかった場合の保険（JSエラー等でナビゲーションが中断したとき用）
    const SKELETON_TIMEOUT_MS = 10000;

    let overlay: HTMLDivElement | null = null;
    let hideTimer: number | undefined;

    const buildOverlay = (): HTMLDivElement => {
        const el = document.createElement('div');
        el.className = 'skeleton-overlay';
        el.setAttribute('aria-hidden', 'true');
        el.innerHTML = [
            '<div class="skeleton-page">',
            '  <div class="sk sk-title"></div>',
            '  <div class="sk sk-block"></div>',
            '  <div class="sk-grid">',
            '    <div class="sk sk-card"></div>',
            '    <div class="sk sk-card"></div>',
            '    <div class="sk sk-card"></div>',
            '    <div class="sk sk-card"></div>',
            '  </div>',
            '</div>',
        ].join('');
        return el;
    };

    const hideSkeleton = (): void => {
        window.clearTimeout(hideTimer);
        if (overlay) {
            overlay.classList.remove('show');
        }
    };

    const showSkeleton = (): void => {
        if (!overlay) {
            overlay = buildOverlay();
            document.body.appendChild(overlay);
        }
        overlay.classList.add('show');
        window.clearTimeout(hideTimer);
        hideTimer = window.setTimeout(hideSkeleton, SKELETON_TIMEOUT_MS);
    };

    document.addEventListener('click', (event: MouseEvent) => {
        // 修飾キー付き・別ハンドラー処理済み（モーダル表示やデモモード等）は対象外
        if (event.defaultPrevented || event.button !== 0) {
            return;
        }
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }
        const target = event.target instanceof Element ? event.target : null;
        const anchor = target ? target.closest('a[href]') : null;
        if (!(anchor instanceof HTMLAnchorElement)) {
            return;
        }
        if (anchor.target && anchor.target !== '_self') {
            return;
        }
        if (anchor.hasAttribute('download') || anchor.getAttribute('data-toggle') !== null) {
            return;
        }
        const href = anchor.getAttribute('href') ?? '';
        if (href === '' || href.startsWith('#') || href.startsWith('javascript:')) {
            return;
        }
        let url: URL;
        try {
            url = new URL(anchor.href, window.location.href);
        } catch (e) {
            return;
        }
        if (url.origin !== window.location.origin) {
            return;
        }
        // 同一ページ内のアンカー移動は対象外
        if (
            url.pathname === window.location.pathname &&
            url.search === window.location.search &&
            url.hash !== ''
        ) {
            return;
        }
        showSkeleton();
    });

    document.addEventListener('submit', (event: Event) => {
        // fetch で処理されるフォームは preventDefault 済みのため対象外
        if (event.defaultPrevented) {
            return;
        }
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        if (form.target && form.target !== '_self') {
            return;
        }
        showSkeleton();
    });

    // 戻るボタン（bfcache 復元）で前のページに戻ったときは必ず消す
    window.addEventListener('pageshow', () => {
        hideSkeleton();
    });
})();
