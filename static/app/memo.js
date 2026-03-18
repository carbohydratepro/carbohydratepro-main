"use strict";
// メモ管理用JavaScript
// メモの展開/折りたたみ
function toggleMemoExpand(memoId) {
    const preview = document.getElementById(`preview-${memoId}`);
    const fullContent = document.getElementById(`full-content-${memoId}`);
    const icon = document.getElementById(`icon-${memoId}`);
    if (!fullContent)
        return;
    if (fullContent.style.display === 'none') {
        renderMemoContent(fullContent);
        if (preview)
            preview.style.display = 'none';
        fullContent.style.display = 'block';
        if (icon)
            icon.classList.add('expanded');
    }
    else {
        if (preview)
            preview.style.display = 'block';
        fullContent.style.display = 'none';
        if (icon)
            icon.classList.remove('expanded');
    }
}
let markdownEnabled = false;
let memoMdRenderer = null;
function renderMemoContent(fullContentEl) {
    var _a;
    if (!fullContentEl)
        return;
    let raw = '';
    if (fullContentEl.dataset.rawId) {
        const source = document.getElementById(fullContentEl.dataset.rawId);
        raw = source ? source.value : '';
    }
    else if (fullContentEl.dataset.raw) {
        raw = decodeURIComponent(fullContentEl.dataset.raw);
    }
    if (markdownEnabled) {
        if (!memoMdRenderer) {
            if (window.markdownit) {
                memoMdRenderer = window.markdownit({ html: false, linkify: true, breaks: true });
            }
            else if (window.memoMarkdownRender) {
                memoMdRenderer = { render: window.memoMarkdownRender };
            }
        }
        const rendered = memoMdRenderer ? memoMdRenderer.render(raw) : raw;
        fullContentEl.innerHTML = rendered;
    }
    else {
        fullContentEl.textContent = raw;
        fullContentEl.innerHTML = ((_a = fullContentEl.textContent) !== null && _a !== void 0 ? _a : '').replace(/\n/g, '<br>');
    }
}
function setMarkdownMode(enabled) {
    markdownEnabled = enabled;
    localStorage.setItem('memoMarkdownEnabled', enabled ? '1' : '0');
    const onBtn = document.getElementById('markdownToggleOn');
    const offBtn = document.getElementById('markdownToggleOff');
    if (onBtn && offBtn) {
        if (enabled) {
            onBtn.classList.add('btn-primary');
            onBtn.classList.remove('btn-outline-secondary');
            offBtn.classList.add('btn-outline-secondary');
            offBtn.classList.remove('btn-primary');
        }
        else {
            offBtn.classList.add('btn-primary');
            offBtn.classList.remove('btn-outline-secondary');
            onBtn.classList.add('btn-outline-secondary');
            onBtn.classList.remove('btn-primary');
        }
    }
    document.querySelectorAll('.memo-full-content').forEach(el => {
        if (el.style.display !== 'none') {
            renderMemoContent(el);
        }
    });
}
// お気に入りの切り替え
function toggleFavorite(memoId, button) {
    var _a;
    fetch(`/carbohydratepro/memos/toggle-favorite/${memoId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': ((_a = document.querySelector('[name=csrfmiddlewaretoken]')) === null || _a === void 0 ? void 0 : _a.value) || '',
            'Content-Type': 'application/json',
        },
    })
        .then(response => response.json())
        .then(data => {
        if (data.success) {
            const icon = button.querySelector('i');
            if (data.is_favorite) {
                if (icon)
                    icon.className = 'fas fa-star';
                button.setAttribute('data-favorite', 'true');
                button.setAttribute('title', 'お気に入り解除');
            }
            else {
                if (icon)
                    icon.className = 'far fa-star';
                button.setAttribute('data-favorite', 'false');
                button.setAttribute('title', 'お気に入り');
            }
            setTimeout(() => location.reload(), 500);
        }
    })
        .catch(error => console.error('Error:', error));
}
// フォームデータをURLSearchParams形式に変換
function serializeMemoForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}
// 編集モーダル関連
async function openEditMemoModal(memoId) {
    try {
        const response = await fetch(`/carbohydratepro/memos/edit/${memoId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#editMemoModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#editMemoModal').modal('show');
        const form = document.getElementById('editMemoForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                try {
                    const res = await fetch(form.action, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: serializeMemoForm(form),
                    });
                    const data = await res.json();
                    if (data.success) {
                        $('#editMemoModal').modal('hide');
                        location.reload();
                    }
                    else {
                        alert('エラーが発生しました。入力内容を確認してください。');
                    }
                }
                catch (_a) {
                    alert('保存に失敗しました。');
                }
            });
        }
    }
    catch (_a) {
        alert('データの読み込みに失敗しました。');
    }
}
// 新規作成モーダル関連
async function openCreateMemoModal() {
    try {
        const response = await fetch('/carbohydratepro/memos/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#createMemoModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#createMemoModal').modal('show');
        const form = document.getElementById('createMemoForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                try {
                    const res = await fetch(form.action, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: serializeMemoForm(form),
                    });
                    const data = await res.json();
                    if (data.success) {
                        $('#createMemoModal').modal('hide');
                        location.reload();
                    }
                    else {
                        alert('エラーが発生しました。入力内容を確認してください。');
                    }
                }
                catch (_a) {
                    alert('保存に失敗しました。');
                }
            });
        }
    }
    catch (_a) {
        alert('データの読み込みに失敗しました。');
    }
}
// フィルター関連のイベント処理
function initializeMemoFilters() {
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            filterForm.submit();
        });
    }
    const memoTypeFilter = document.getElementById('memo_type_filter');
    memoTypeFilter === null || memoTypeFilter === void 0 ? void 0 : memoTypeFilter.addEventListener('change', () => {
        var _a;
        (_a = document.getElementById('filterForm')) === null || _a === void 0 ? void 0 : _a.submit();
    });
    const favoriteFilter = document.getElementById('favorite_filter');
    favoriteFilter === null || favoriteFilter === void 0 ? void 0 : favoriteFilter.addEventListener('change', () => {
        var _a;
        (_a = document.getElementById('filterForm')) === null || _a === void 0 ? void 0 : _a.submit();
    });
    const searchInput = document.getElementById('search');
    searchInput === null || searchInput === void 0 ? void 0 : searchInput.addEventListener('keypress', (e) => {
        var _a;
        if (e.key === 'Enter') {
            e.preventDefault();
            (_a = document.getElementById('filterForm')) === null || _a === void 0 ? void 0 : _a.submit();
        }
    });
}
function initMemoDoubleClick() {
    document.querySelectorAll('.memo-card[data-item-id]').forEach(card => {
        var _a;
        const memoId = (_a = card.dataset['itemId']) !== null && _a !== void 0 ? _a : '';
        if (!memoId)
            return;
        let lastTapTime = 0;
        let suppressClick = false;
        let clickCount = 0;
        let clickTimer = null;
        card.addEventListener('touchend', (e) => {
            const el = e.target;
            if (isInteractiveTarget(el) || !!el.closest('.memo-preview') || card.classList.contains('delete-pending'))
                return;
            const now = Date.now();
            if (now - lastTapTime < 400) {
                e.preventDefault();
                suppressClick = true;
                lastTapTime = 0;
                openEditMemoModal(memoId);
            }
            else {
                lastTapTime = now;
            }
        }, { passive: false });
        card.addEventListener('click', (e) => {
            if (suppressClick) {
                suppressClick = false;
                return;
            }
            const el = e.target;
            if (isInteractiveTarget(el) || !!el.closest('.memo-preview') || card.classList.contains('delete-pending'))
                return;
            clickCount++;
            if (clickCount === 1) {
                clickTimer = setTimeout(() => { clickCount = 0; }, 400);
            }
            else if (clickCount >= 2) {
                if (clickTimer !== null)
                    clearTimeout(clickTimer);
                clickCount = 0;
                openEditMemoModal(memoId);
            }
        });
    });
}
// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeMemoFilters();
    const saved = localStorage.getItem('memoMarkdownEnabled');
    setMarkdownMode(saved === '1');
    initLongPressDelete();
    initMemoDoubleClick();
});
