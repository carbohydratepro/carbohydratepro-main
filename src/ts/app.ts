// 長押し削除ユーティリティ（全画面共通）
const LP_DELETE_DURATION = 400;

function isInteractiveTarget(target: EventTarget | null): boolean {
    if (!target) return false;
    const el = target as HTMLElement;
    return !!(
        el.closest('button') ||
        el.closest('input') ||
        el.closest('select') ||
        el.closest('textarea') ||
        el.closest('a') ||
        el.closest('.lp-delete-overlay')
    );
}

function attachLongPressDelete(item: HTMLElement): void {
    let timerId: ReturnType<typeof setTimeout> | null = null;
    let deletePending = false;
    let touchStartX = 0;
    let touchStartY = 0;

    const overlay = item.querySelector<HTMLElement>('.lp-delete-overlay');

    function activateDelete(): void {
        deletePending = true;
        item.classList.add('delete-pending');
        if (navigator.vibrate) navigator.vibrate(50);
    }

    function deactivateDelete(): void {
        deletePending = false;
        item.classList.remove('delete-pending');
    }

    function startTimer(): void {
        timerId = setTimeout(activateDelete, LP_DELETE_DURATION);
    }

    function cancelTimer(): void {
        if (timerId !== null) {
            clearTimeout(timerId);
            timerId = null;
        }
    }

    if (overlay) {
        overlay.addEventListener('click', async (e: MouseEvent) => {
            e.stopPropagation();
            e.preventDefault();
            if (!deletePending) return;

            const modalId = item.dataset['deleteModalId'];
            if (modalId) {
                deactivateDelete();
                $('#' + modalId).modal('show');
                return;
            }

            const deleteUrl = item.dataset['deleteUrl'];
            if (!deleteUrl) return;
            try {
                const res = await fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken') ?? '',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                });
                if (res.ok) {
                    location.reload();
                }
            } catch (err) {
                console.error('Delete failed:', err);
                deactivateDelete();
            }
        });
    }

    document.addEventListener('click', (e: MouseEvent) => {
        if (deletePending && !item.contains(e.target as Node)) {
            deactivateDelete();
        }
    });

    // ダブルタップで編集モーダルを開く（data-edit-modal-id が設定されている場合）
    const editModalId = item.dataset['editModalId'];
    if (editModalId) {
        let editLastTap = 0;
        let editSuppressClick = false;
        let editClickCount = 0;
        let editClickTimer: ReturnType<typeof setTimeout> | null = null;

        item.addEventListener('touchend', (e: TouchEvent) => {
            const el = e.target as HTMLElement;
            if (isInteractiveTarget(el) || item.classList.contains('delete-pending')) return;
            const now = Date.now();
            if (now - editLastTap < 400) {
                e.preventDefault();
                editSuppressClick = true;
                editLastTap = 0;
                $('#' + editModalId).modal('show');
            } else {
                editLastTap = now;
            }
        }, { passive: false });

        item.addEventListener('click', (e: MouseEvent) => {
            if (editSuppressClick) { editSuppressClick = false; return; }
            const el = e.target as HTMLElement;
            if (isInteractiveTarget(el) || item.classList.contains('delete-pending')) return;
            editClickCount++;
            if (editClickCount === 1) {
                editClickTimer = setTimeout(() => { editClickCount = 0; }, 400);
            } else if (editClickCount >= 2) {
                if (editClickTimer !== null) clearTimeout(editClickTimer);
                editClickCount = 0;
                $('#' + editModalId).modal('show');
            }
        });
    }

    item.addEventListener('mousedown', (e: MouseEvent) => {
        if (isInteractiveTarget(e.target)) return;
        startTimer();
    });
    item.addEventListener('mouseup', cancelTimer);
    item.addEventListener('mouseleave', cancelTimer);
    item.addEventListener('dragstart', cancelTimer);

    item.addEventListener('touchstart', (e: TouchEvent) => {
        if (isInteractiveTarget(e.target)) return;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        startTimer();
    }, { passive: true });
    item.addEventListener('touchend', cancelTimer);
    item.addEventListener('touchcancel', cancelTimer);
    item.addEventListener('touchmove', (e: TouchEvent) => {
        const dx = Math.abs(e.touches[0].clientX - touchStartX);
        const dy = Math.abs(e.touches[0].clientY - touchStartY);
        if (dx > 10 || dy > 10) cancelTimer();
    }, { passive: true });
}

function initLongPressDelete(container: HTMLElement = document.body): void {
    container.querySelectorAll<HTMLElement>('.lp-delete-item, .lp-delete-modal-item').forEach(item => {
        attachLongPressDelete(item);
    });
}

function getCookie(name: string): string | null {
    if (!document.cookie || document.cookie === '') return null;
    const found = document.cookie.split(';')
        .map(c => c.trim())
        .find(c => c.startsWith(`${name}=`));
    return found ? decodeURIComponent(found.substring(name.length + 1)) : null;
}

const csrftoken = getCookie('csrftoken');

// メッセージダイアログを自動表示
document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('messageDialog');
    if (dialog) {
        dialog.style.display = 'flex';
        setTimeout(() => dialog.classList.add('show'), 10);
        setTimeout(() => closeMessageDialog(), 5000);
    }
});

// ダイアログを閉じる
function closeMessageDialog(): void {
    const dialog = document.getElementById('messageDialog');
    if (dialog) {
        dialog.classList.remove('show');
        setTimeout(() => { dialog.style.display = 'none'; }, 300);
    }
}

// 背景クリックでダイアログを閉じる
document.addEventListener('click', (e) => {
    const dialog = document.getElementById('messageDialog');
    if (dialog && e.target === dialog) {
        closeMessageDialog();
    }
});

// ESCキーでダイアログを閉じる
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeMessageDialog();
    }
});
