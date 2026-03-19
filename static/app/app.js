"use strict";
// 長押し削除ユーティリティ（全画面共通）
const LP_DELETE_DURATION = 400;
function isInteractiveTarget(target) {
    if (!target)
        return false;
    const el = target;
    return !!(el.closest('button') ||
        el.closest('input') ||
        el.closest('select') ||
        el.closest('textarea') ||
        el.closest('a') ||
        el.closest('.lp-delete-overlay'));
}
function attachLongPressDelete(item) {
    let timerId = null;
    let deletePending = false;
    let touchStartX = 0;
    let touchStartY = 0;
    const overlay = item.querySelector('.lp-delete-overlay');
    function activateDelete() {
        deletePending = true;
        item.classList.add('delete-pending');
        if (navigator.vibrate)
            navigator.vibrate(50);
    }
    function deactivateDelete() {
        deletePending = false;
        item.classList.remove('delete-pending');
    }
    function startTimer() {
        timerId = setTimeout(activateDelete, LP_DELETE_DURATION);
    }
    function cancelTimer() {
        if (timerId !== null) {
            clearTimeout(timerId);
            timerId = null;
        }
    }
    if (overlay) {
        overlay.addEventListener('click', async (e) => {
            var _a;
            e.stopPropagation();
            e.preventDefault();
            if (!deletePending)
                return;
            const modalId = item.dataset['deleteModalId'];
            if (modalId) {
                deactivateDelete();
                $('#' + modalId).modal('show');
                return;
            }
            const deleteUrl = item.dataset['deleteUrl'];
            if (!deleteUrl)
                return;
            try {
                const res = await fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': (_a = getCookie('csrftoken')) !== null && _a !== void 0 ? _a : '',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                });
                if (res.ok) {
                    location.reload();
                }
            }
            catch (err) {
                console.error('Delete failed:', err);
                deactivateDelete();
            }
        });
    }
    document.addEventListener('click', (e) => {
        if (deletePending && !item.contains(e.target)) {
            deactivateDelete();
        }
    });
    // ダブルタップで編集モーダルを開く（data-edit-modal-id が設定されている場合）
    const editModalId = item.dataset['editModalId'];
    if (editModalId) {
        let editLastTap = 0;
        let editSuppressClick = false;
        let editClickCount = 0;
        let editClickTimer = null;
        item.addEventListener('touchend', (e) => {
            const el = e.target;
            if (isInteractiveTarget(el) || item.classList.contains('delete-pending'))
                return;
            const now = Date.now();
            if (now - editLastTap < 400) {
                e.preventDefault();
                editSuppressClick = true;
                editLastTap = 0;
                $('#' + editModalId).modal('show');
            }
            else {
                editLastTap = now;
            }
        }, { passive: false });
        item.addEventListener('click', (e) => {
            if (editSuppressClick) {
                editSuppressClick = false;
                return;
            }
            const el = e.target;
            if (isInteractiveTarget(el) || item.classList.contains('delete-pending'))
                return;
            editClickCount++;
            if (editClickCount === 1) {
                editClickTimer = setTimeout(() => { editClickCount = 0; }, 400);
            }
            else if (editClickCount >= 2) {
                if (editClickTimer !== null)
                    clearTimeout(editClickTimer);
                editClickCount = 0;
                $('#' + editModalId).modal('show');
            }
        });
    }
    item.addEventListener('mousedown', (e) => {
        if (isInteractiveTarget(e.target))
            return;
        startTimer();
    });
    item.addEventListener('mouseup', cancelTimer);
    item.addEventListener('mouseleave', cancelTimer);
    item.addEventListener('dragstart', cancelTimer);
    item.addEventListener('touchstart', (e) => {
        if (isInteractiveTarget(e.target))
            return;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        startTimer();
    }, { passive: true });
    item.addEventListener('touchend', cancelTimer);
    item.addEventListener('touchcancel', cancelTimer);
    item.addEventListener('touchmove', (e) => {
        const dx = Math.abs(e.touches[0].clientX - touchStartX);
        const dy = Math.abs(e.touches[0].clientY - touchStartY);
        if (dx > 10 || dy > 10)
            cancelTimer();
    }, { passive: true });
}
function initLongPressDelete(container = document.body) {
    container.querySelectorAll('.lp-delete-item, .lp-delete-modal-item').forEach(item => {
        attachLongPressDelete(item);
    });
}
function getCookie(name) {
    if (!document.cookie || document.cookie === '')
        return null;
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
function closeMessageDialog() {
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
// 日付・時刻入力: クリック時に必ずピッカーを開く
function initDateTimePickers() {
    document.querySelectorAll('input[type="date"], input[type="time"]').forEach(input => {
        input.addEventListener('click', () => {
            if (typeof input.showPicker === 'function') {
                input.showPicker();
            }
        });
    });
}
document.addEventListener('DOMContentLoaded', () => {
    initDateTimePickers();
    // モーダルが開いた後にも適用
    document.addEventListener('shown.bs.modal', () => {
        initDateTimePickers();
    });
});
