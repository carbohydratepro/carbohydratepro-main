"use strict";
// 買い物リスト管理用JavaScript
function getCsrfToken() {
    var _a;
    return ((_a = document.querySelector('[name=csrfmiddlewaretoken]')) === null || _a === void 0 ? void 0 : _a.value) || '';
}
// 購入済みトグル
async function toggleCheck(itemId) {
    try {
        const response = await fetch(`/carbohydratepro/shopping/toggle-check/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        const data = await response.json();
        if (data.success) {
            const row = document.getElementById(`item-row-${itemId}`);
            const icon = document.querySelector(`#check-btn-${itemId} i`);
            const titleEl = document.getElementById(`item-title-${itemId}`);
            if (data.is_checked) {
                row === null || row === void 0 ? void 0 : row.classList.add('shopping-checked');
                if (icon) {
                    icon.classList.remove('fa-circle', 'text-muted');
                    icon.classList.add('fa-check-circle', 'text-success');
                }
                if (titleEl) {
                    titleEl.classList.add('text-muted');
                    titleEl.style.textDecoration = 'line-through';
                }
            }
            else {
                row === null || row === void 0 ? void 0 : row.classList.remove('shopping-checked');
                if (icon) {
                    icon.classList.remove('fa-check-circle', 'text-success');
                    icon.classList.add('fa-circle', 'text-muted');
                }
                if (titleEl) {
                    titleEl.classList.remove('text-muted');
                    titleEl.style.textDecoration = '';
                }
            }
        }
    }
    catch (_a) {
        console.error('チェック更新に失敗しました');
    }
}
// 残数の更新
function updateCount(itemId, fieldType, action) {
    fetch(`/carbohydratepro/shopping/update-count/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `field_type=${fieldType}&action=${action}`,
    })
        .then(response => response.json())
        .then((data) => {
        if (data.success) {
            const remainingEl = document.getElementById(`remaining-count-${itemId}`);
            if (remainingEl)
                remainingEl.textContent = String(data.remaining_count);
            // ステータスバッジを更新
            const badge = document.getElementById(`status-badge-${itemId}`);
            if (badge) {
                if (data.status_code === 'insufficient') {
                    badge.className = 'badge badge-danger mr-1';
                    badge.textContent = '不足';
                }
                else {
                    badge.className = 'badge badge-success mr-1';
                    badge.textContent = '残あり';
                }
            }
        }
    })
        .catch(error => console.error('Error:', error));
}
// フォームデータをURLSearchParams形式に変換
function serializeShoppingForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}
// 編集モーダル
async function openEditShoppingModal(itemId) {
    try {
        const response = await fetch(`/carbohydratepro/shopping/edit/${itemId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#editShoppingModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#editShoppingModal').modal('show');
        const form = document.getElementById('editShoppingItemForm');
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
                        body: serializeShoppingForm(form),
                    });
                    const data = await res.json();
                    if (data.success) {
                        $('#editShoppingModal').modal('hide');
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
// 新規作成モーダル
async function openCreateShoppingModal() {
    try {
        const response = await fetch('/carbohydratepro/shopping/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#createShoppingModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#createShoppingModal').modal('show');
        const form = document.getElementById('createShoppingItemForm');
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
                        body: serializeShoppingForm(form),
                    });
                    const data = await res.json();
                    if (data.success) {
                        $('#createShoppingModal').modal('hide');
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
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('input[name="search"]');
    searchInput === null || searchInput === void 0 ? void 0 : searchInput.addEventListener('keypress', (e) => {
        var _a;
        if (e.key === 'Enter') {
            (_a = searchInput.closest('form')) === null || _a === void 0 ? void 0 : _a.submit();
        }
    });
});
