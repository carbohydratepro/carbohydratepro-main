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
        if (memoMdRenderer)
            fullContentEl.innerHTML = memoMdRenderer.render(raw);
        else
            fullContentEl.textContent = raw;
    }
    else {
        fullContentEl.textContent = raw;
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
    if (!(button instanceof HTMLButtonElement) || button.disabled)
        return;
    button.disabled = true;
    fetch(`/carbohydratepro/memos/toggle-favorite/${memoId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': ((_a = document.querySelector('[name=csrfmiddlewaretoken]')) === null || _a === void 0 ? void 0 : _a.value) || '',
            'Content-Type': 'application/json',
        },
    })
        .then(response => { if (!response.ok)
        throw new Error('request'); return response.json(); })
        .then(data => {
        if (data.success) {
            button.setAttribute('aria-pressed', String(data.is_favorite));
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
            showToast(data.is_favorite ? 'お気に入りに追加しました。' : 'お気に入りを解除しました。', 'success');
            if (!data.is_favorite && new URL(location.href).searchParams.get('favorite') === 'true')
                location.reload();
        }
        else {
            throw new Error('request');
        }
    })
        .catch(error => { if (!(error instanceof Error && error.message === 'demo'))
        showToast('変更できませんでした。もう一度お試しください。', 'error'); })
        .then(() => { button.disabled = false; });
}
// フォームデータをURLSearchParams形式に変換
function serializeMemoForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}
// 試作: 共通の読み込み・保存状態と、入力を失わないエラー表示。
let memoOpening = false;
async function openMemoEditor(url, modalId) {
    var _a, _b, _c;
    if (memoOpening)
        return;
    memoOpening = true;
    const active = document.activeElement;
    const opener = (_b = (_a = active === null || active === void 0 ? void 0 : active.closest('.memo-item-actions')) === null || _a === void 0 ? void 0 : _a.querySelector('[data-toggle="dropdown"]')) !== null && _b !== void 0 ? _b : active;
    try {
        const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!response.ok || response.redirected)
            throw new Error('load');
        const html = await response.text();
        const dialog = document.querySelector(modalId + ' .modal-dialog');
        if (!dialog)
            return;
        dialog.innerHTML = html;
        const form = dialog.querySelector('form');
        if (!form)
            return;
        const title = dialog.querySelector('.modal-title');
        if (title)
            title.id = modalId.slice(1) + 'Label';
        const notice = document.createElement('div');
        notice.className = 'alert alert-danger d-none';
        notice.setAttribute('role', 'alert');
        (_c = form.querySelector('.modal-body')) === null || _c === void 0 ? void 0 : _c.prepend(notice);
        $(modalId).one('shown.bs.modal', () => {
            var _a;
            (_a = form.querySelector('[name="title"]')) === null || _a === void 0 ? void 0 : _a.focus();
        });
        $(modalId).one('hidden.bs.modal', () => {
            if (opener instanceof HTMLElement && opener.isConnected)
                opener.focus();
        });
        $(modalId).modal('show');
        form.addEventListener('submit', async (event) => {
            var _a, _b, _c;
            event.preventDefault();
            if (form.dataset.saving === 'true')
                return;
            form.dataset.saving = 'true';
            form.setAttribute('aria-busy', 'true');
            notice.classList.add('d-none');
            form.querySelectorAll('.memo-field-error').forEach(el => el.remove());
            form.querySelectorAll('[aria-invalid]').forEach(el => {
                el.removeAttribute('aria-invalid');
                el.removeAttribute('aria-describedby');
            });
            const submit = form.querySelector('[type="submit"]');
            const label = (_a = submit === null || submit === void 0 ? void 0 : submit.textContent) !== null && _a !== void 0 ? _a : '保存';
            const body = serializeMemoForm(form);
            // 保存中は閉じる・編集を止めて、結果と画面の食い違いを防ぐ。
            const controls = Array.from(dialog.querySelectorAll('input, button, select, textarea'));
            const enabled = controls.filter(el => !el.disabled);
            enabled.forEach(el => { el.disabled = true; });
            if (submit)
                submit.textContent = '保存中…';
            const preventClose = (e) => { if (form.dataset.saving === 'true')
                e.preventDefault(); };
            $(modalId).on('hide.bs.modal', preventClose);
            let saved = false;
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded' },
                    body,
                });
                if (!response.ok || response.redirected)
                    throw new Error('save');
                const data = await response.json();
                if (data.success) {
                    saved = true;
                    try {
                        sessionStorage.setItem('memoSavedNotice', '1');
                    }
                    catch ( /* 保存自体は成功済み */_d) { /* 保存自体は成功済み */ }
                    location.reload();
                }
                else {
                    notice.textContent = '入力内容を確認してください。';
                    notice.classList.remove('d-none');
                    Object.entries((_b = data.errors) !== null && _b !== void 0 ? _b : {}).forEach(([name, errors]) => {
                        var _a;
                        const field = form.elements.namedItem(name);
                        if (!(field instanceof HTMLElement))
                            return;
                        const error = document.createElement('div');
                        error.className = 'memo-field-error text-danger small mt-1';
                        error.id = modalId.slice(1) + '-' + name + '-error';
                        error.textContent = errors.join(' ');
                        field.setAttribute('aria-invalid', 'true');
                        field.setAttribute('aria-describedby', error.id);
                        (_a = field.closest('.form-group')) === null || _a === void 0 ? void 0 : _a.append(error);
                    });
                }
            }
            catch (_e) {
                notice.textContent = '保存結果を確認できませんでした。入力内容は残しています。再送前に別タブの一覧で保存済みか確認してください。';
                notice.classList.remove('d-none');
            }
            finally {
                if (!saved) {
                    form.dataset.saving = 'false';
                    form.removeAttribute('aria-busy');
                    enabled.forEach(el => { el.disabled = false; });
                    if (submit)
                        submit.textContent = label;
                    (_c = form.querySelector('[aria-invalid="true"]')) === null || _c === void 0 ? void 0 : _c.focus();
                }
                $(modalId).off('hide.bs.modal', preventClose);
            }
        });
    }
    catch (error) {
        if (!(error instanceof Error && error.message === 'demo'))
            showToast('メモを読み込めませんでした。もう一度お試しください。', 'error');
    }
    finally {
        memoOpening = false;
    }
}
async function openEditMemoModal(memoId) {
    await openMemoEditor('/carbohydratepro/memos/edit/' + memoId + '/', '#editMemoModal');
}
async function openCreateMemoModal() {
    await openMemoEditor('/carbohydratepro/memos/create/', '#createMemoModal');
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
    document.querySelectorAll('[data-memo-notice]').forEach(notice => {
        var _a;
        showToast((_a = notice.textContent) !== null && _a !== void 0 ? _a : '', notice.dataset.noticeType === 'error' ? 'error' : 'success');
        notice.remove();
    });
    if (sessionStorage.getItem('memoSavedNotice') === '1') {
        sessionStorage.removeItem('memoSavedNotice');
        showToast('メモを保存しました。', 'success');
    }
    document.addEventListener('click', event => {
        var _a, _b;
        const target = event.target instanceof Element ? event.target.closest('[data-memo-delete-url]') : null;
        if (!target)
            return;
        const form = document.getElementById('deleteMemoForm');
        if (form instanceof HTMLFormElement)
            form.action = (_a = target.dataset.memoDeleteUrl) !== null && _a !== void 0 ? _a : '';
        const name = document.getElementById('deleteMemoName');
        if (name)
            name.textContent = (_b = target.dataset.memoTitle) !== null && _b !== void 0 ? _b : '';
    });
    initializeMemoFilters();
    const saved = localStorage.getItem('memoMarkdownEnabled');
    setMarkdownMode(saved === '1');
    initLongPressDelete();
    initMemoDoubleClick();
});
