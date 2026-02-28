// 買い物リスト管理用JavaScript

interface UpdateCountResponse {
  success: boolean;
  remaining_count: number;
  threshold_count: number;
}

interface ShoppingModalResponse {
  success: boolean;
}

// 残数・不足数の更新（+/-/+10/-10ボタン用）
function updateCount(itemId: string, fieldType: string, action: string): void {
    fetch(`/carbohydratepro/shopping/update-count/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value || '',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `field_type=${fieldType}&action=${action}`,
    })
    .then(response => response.json())
    .then((data: UpdateCountResponse) => {
        if (data.success) {
            // デスクトップ版の残数と不足数の表示を更新
            const remainingDesktop = document.getElementById(`remaining-count-${itemId}`);
            const thresholdDesktop = document.getElementById(`threshold-count-${itemId}`);
            if (remainingDesktop) remainingDesktop.textContent = String(data.remaining_count);
            if (thresholdDesktop) thresholdDesktop.textContent = String(data.threshold_count);

            // モバイル版の残数と不足数の表示を更新
            const remainingMobile = document.getElementById(`remaining-count-mobile-${itemId}`);
            const thresholdMobile = document.getElementById(`threshold-count-mobile-${itemId}`);
            if (remainingMobile) remainingMobile.textContent = String(data.remaining_count);
            if (thresholdMobile) thresholdMobile.textContent = String(data.threshold_count);

            // カードの枠線の色を更新
            updateCardBorder(itemId, data.remaining_count, data.threshold_count);
        }
    })
    .catch(error => console.error('Error:', error));
}

// カードの枠線の色を更新する共通関数
function updateCardBorder(itemId: string, remainingCount: number, thresholdCount: number): void {
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
function serializeShoppingForm(form: HTMLFormElement): string {
    return new URLSearchParams(new FormData(form) as unknown as Record<string, string>).toString();
}

// 編集モーダル関連
async function openEditShoppingModal(itemId: string): Promise<void> {
    try {
        const response = await fetch(`/carbohydratepro/shopping/edit/${itemId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#editShoppingModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
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
                    const data: ShoppingModalResponse = await res.json();
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
        }
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 新規作成モーダル関連
async function openCreateShoppingModal(): Promise<void> {
    try {
        const response = await fetch('/carbohydratepro/shopping/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#createShoppingModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
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
                    const data: ShoppingModalResponse = await res.json();
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
        }
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// フィルター関連のイベント処理
function initializeShoppingFilters(): void {
    const searchForm = document.getElementById('searchForm') as HTMLFormElement | null;
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
            (document.getElementById('searchForm') as HTMLFormElement | null)?.submit();
        }
    });
}

// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeShoppingFilters();
});
