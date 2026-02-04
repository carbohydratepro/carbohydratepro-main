// 買い物リスト管理用JavaScript

// 残数・不足数の更新（+/-/+10/-10ボタン用）
function updateCount(itemId, fieldType, action) {
    fetch(`/carbohydratepro/shopping/update-count/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `field_type=${fieldType}&action=${action}`,
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // デスクトップ版の残数と不足数の表示を更新
            const remainingDesktop = document.getElementById(`remaining-count-${itemId}`);
            const thresholdDesktop = document.getElementById(`threshold-count-${itemId}`);
            if (remainingDesktop) remainingDesktop.textContent = data.remaining_count;
            if (thresholdDesktop) thresholdDesktop.textContent = data.threshold_count;

            // モバイル版の残数と不足数の表示を更新
            const remainingMobile = document.getElementById(`remaining-count-mobile-${itemId}`);
            const thresholdMobile = document.getElementById(`threshold-count-mobile-${itemId}`);
            if (remainingMobile) remainingMobile.textContent = data.remaining_count;
            if (thresholdMobile) thresholdMobile.textContent = data.threshold_count;

            // カードの枠線の色を更新
            updateCardBorder(itemId, data.remaining_count, data.threshold_count);
        }
    })
    .catch(error => console.error('Error:', error));
}

// カードの枠線の色を更新する共通関数
function updateCardBorder(itemId, remainingCount, thresholdCount) {
    const card = document.getElementById(`remaining-count-${itemId}`)?.closest('.shopping-item-card');
    if (!card) return;

    card.classList.remove('border-success', 'border-danger');

    if (thresholdCount >= 1) {
        card.classList.add('border-danger');
    } else if (thresholdCount === 0 && remainingCount >= 1) {
        card.classList.add('border-success');
    }
}

// フォームデータをURLSearchParams形式に変換
function serializeShoppingForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}

// 編集モーダル関連
async function openEditShoppingModal(itemId) {
    try {
        const response = await fetch(`/carbohydratepro/shopping/edit/${itemId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#editShoppingModal .modal-dialog').innerHTML = html;
        $('#editShoppingModal').modal('show');

        const form = document.getElementById('editShoppingItemForm');
        form?.addEventListener('submit', async (e) => {
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
                } else {
                    alert('エラーが発生しました。入力内容を確認してください。');
                }
            } catch {
                alert('保存に失敗しました。');
            }
        });
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 新規作成モーダル関連
async function openCreateShoppingModal() {
    try {
        const response = await fetch('/carbohydratepro/shopping/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#createShoppingModal .modal-dialog').innerHTML = html;
        $('#createShoppingModal').modal('show');

        const form = document.getElementById('createShoppingItemForm');
        form?.addEventListener('submit', async (e) => {
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
                } else {
                    alert('エラーが発生しました。入力内容を確認してください。');
                }
            } catch {
                alert('保存に失敗しました。');
            }
        });
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// フィルター関連のイベント処理
function initializeShoppingFilters() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            searchForm.submit();
        });
    }

    const searchInput = document.getElementById('search');
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('searchForm').submit();
        }
    });
}

// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeShoppingFilters();
});
