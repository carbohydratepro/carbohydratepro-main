// トースト通知（全画面共通）
// 主に「削除 → 元に戻す（Undo）」の安全網として使う。
// 削除は即座にUIから消し、数秒間だけ本削除を保留する。Undoで復活、
// タイムアウトで本削除を確定する。ページ離脱時は保留中の削除を確定する。

type ToastType = 'info' | 'success' | 'error';

interface UndoToastOptions {
    message: string;
    durationMs?: number;
    onUndo: () => void;    // 「元に戻す」タップ時に呼ぶ（UIを復元する）
    onCommit: () => void;  // タイムアウト／離脱時に呼ぶ（本削除を実行する）
}

interface ConfirmOptions {
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    danger?: boolean;        // 破壊的操作（確定ボタンを赤くする）
    onConfirm: () => void;
    onCancel?: () => void;
}

// 保留中の確定処理（ページ離脱時にまとめて実行する）
const pendingCommits = new Set<() => void>();

// アプリ内の確認ダイアログ（window.confirm の代替）。
// window.confirm はブラウザ操作をブロックし固着することがあるため、これに置き換える。
function showConfirm(options: ConfirmOptions): void {
    const overlay = document.createElement('div');
    overlay.className = 'app-confirm-overlay';

    const dialog = document.createElement('div');
    dialog.className = 'app-confirm-dialog';
    dialog.setAttribute('role', 'alertdialog');
    dialog.setAttribute('aria-modal', 'true');

    const text = document.createElement('p');
    text.className = 'app-confirm-message';
    text.textContent = options.message;

    const actions = document.createElement('div');
    actions.className = 'app-confirm-actions';

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'btn btn-secondary app-confirm-cancel';
    cancelBtn.textContent = options.cancelLabel ?? 'キャンセル';

    const confirmBtn = document.createElement('button');
    confirmBtn.type = 'button';
    confirmBtn.className = 'btn ' + (options.danger ? 'btn-danger' : 'btn-primary') + ' app-confirm-ok';
    confirmBtn.textContent = options.confirmLabel ?? 'OK';

    actions.append(cancelBtn, confirmBtn);
    dialog.append(text, actions);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));

    let settled = false;
    const close = (confirmed: boolean): void => {
        if (settled) return;
        settled = true;
        document.removeEventListener('keydown', onKey);
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 200);
        if (confirmed) options.onConfirm();
        else options.onCancel?.();
    };

    function onKey(e: KeyboardEvent): void {
        if (e.key === 'Escape') close(false);
    }

    cancelBtn.addEventListener('click', () => close(false));
    confirmBtn.addEventListener('click', () => close(true));
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(false); });
    document.addEventListener('keydown', onKey);
    cancelBtn.focus();
}

function ensureToastContainer(): HTMLElement {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
    }
    return container;
}

function buildToast(type: ToastType): HTMLDivElement {
    const toast = document.createElement('div');
    toast.className = `app-toast app-toast-${type}`;
    toast.setAttribute('role', 'status');
    return toast;
}

function dismissToast(toast: HTMLElement): void {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 250);
}

// 単純な通知トースト
function showToast(message: string, type: ToastType = 'info', durationMs = 4000): void {
    const container = ensureToastContainer();
    const toast = buildToast(type);

    const text = document.createElement('span');
    text.className = 'app-toast-text';
    text.textContent = message;
    toast.appendChild(text);

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'app-toast-close';
    closeBtn.setAttribute('aria-label', '閉じる');
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => dismissToast(toast));
    toast.appendChild(closeBtn);

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    if (durationMs > 0) {
        setTimeout(() => dismissToast(toast), durationMs);
    }
}

// Undo付きトースト。削除の取り消しに使う。
function showUndoToast(options: UndoToastOptions): void {
    const durationMs = options.durationMs ?? 5000;
    const container = ensureToastContainer();
    const toast = buildToast('info');

    let settled = false;
    let timerId: ReturnType<typeof setTimeout> | null = null;

    // 確定（本削除）。保留セットから外して一度だけ実行する。
    const commit = (): void => {
        if (settled) return;
        settled = true;
        if (timerId !== null) clearTimeout(timerId);
        pendingCommits.delete(commit);
        options.onCommit();
    };

    // 取り消し（UI復元）。本削除は行わない。
    const undo = (): void => {
        if (settled) return;
        settled = true;
        if (timerId !== null) clearTimeout(timerId);
        pendingCommits.delete(commit);
        options.onUndo();
        dismissToast(toast);
    };

    pendingCommits.add(commit);

    const text = document.createElement('span');
    text.className = 'app-toast-text';
    text.textContent = options.message;
    toast.appendChild(text);

    const undoBtn = document.createElement('button');
    undoBtn.type = 'button';
    undoBtn.className = 'app-toast-undo';
    undoBtn.textContent = '元に戻す';
    undoBtn.addEventListener('click', undo);
    toast.appendChild(undoBtn);

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));

    timerId = setTimeout(() => {
        commit();
        dismissToast(toast);
    }, durationMs);
}

// ページ離脱時に保留中の削除を確定する（Undoしなかった削除は実行する）
window.addEventListener('pagehide', () => {
    pendingCommits.forEach(commit => commit());
    pendingCommits.clear();
});
