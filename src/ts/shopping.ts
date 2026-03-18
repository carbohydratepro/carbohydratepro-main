// 買い物リスト管理用JavaScript

interface UpdateCountResponse {
    success: boolean;
    remaining_count: number;
    threshold_count: number;
    status: string;
    status_code: string;
}

interface ShoppingModalResponse {
    success: boolean;
}

interface ToggleCheckResponse {
    success: boolean;
    is_checked: boolean;
}

function getCsrfToken(): string {
    return document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value || '';
}

// 購入済みトグル
async function toggleCheck(itemId: number): Promise<void> {
    try {
        const response = await fetch(`/carbohydratepro/shopping/toggle-check/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        const data = await response.json() as ToggleCheckResponse;
        if (data.success) {
            const row = document.getElementById(`item-row-${itemId}`);
            const icon = document.querySelector<HTMLElement>(`#check-btn-${itemId} i`);
            const titleEl = document.getElementById(`item-title-${itemId}`);

            if (data.is_checked) {
                row?.classList.add('shopping-checked');
                if (icon) {
                    icon.classList.remove('fa-circle', 'text-muted');
                    icon.classList.add('fa-check-circle', 'text-success');
                }
                if (titleEl) {
                    titleEl.classList.add('text-muted');
                    titleEl.style.textDecoration = 'line-through';
                }
            } else {
                row?.classList.remove('shopping-checked');
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
    } catch {
        console.error('チェック更新に失敗しました');
    }
}

// 残数の更新
function updateCount(itemId: number, fieldType: string, action: string): void {
    fetch(`/carbohydratepro/shopping/update-count/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `field_type=${fieldType}&action=${action}`,
    })
    .then(response => response.json())
    .then((data: UpdateCountResponse) => {
        if (data.success) {
            const remainingEl = document.getElementById(`remaining-count-${itemId}`);
            if (remainingEl) remainingEl.textContent = String(data.remaining_count);

            // ステータスバッジを更新
            const badge = document.getElementById(`status-badge-${itemId}`);
            if (badge) {
                if (data.status_code === 'insufficient') {
                    badge.className = 'badge badge-danger mr-1';
                    badge.textContent = '不足';
                } else {
                    badge.className = 'badge badge-success mr-1';
                    badge.textContent = '残あり';
                }
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

// フォームデータをURLSearchParams形式に変換
function serializeShoppingForm(form: HTMLFormElement): string {
    return new URLSearchParams(new FormData(form) as unknown as Record<string, string>).toString();
}

// 編集モーダル
async function openEditShoppingModal(itemId: number): Promise<void> {
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

// 新規作成モーダル
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

function initShoppingDoubleClick(): void {
    document.querySelectorAll<HTMLElement>('.lp-delete-item[data-item-id]').forEach(item => {
        const itemId = parseInt(item.dataset['itemId'] ?? '0', 10);
        if (!itemId) return;

        let lastTapTime = 0;
        let suppressClick = false;
        let clickCount = 0;
        let clickTimer: ReturnType<typeof setTimeout> | null = null;

        item.addEventListener('touchend', (e: TouchEvent) => {
            const target = e.target as HTMLElement;
            if (isInteractiveTarget(target) || item.classList.contains('delete-pending')) return;
            const now = Date.now();
            if (now - lastTapTime < 400) {
                e.preventDefault();
                suppressClick = true;
                lastTapTime = 0;
                openEditShoppingModal(itemId);
            } else {
                lastTapTime = now;
            }
        }, { passive: false });

        item.addEventListener('click', (e: MouseEvent) => {
            if (suppressClick) { suppressClick = false; return; }
            const target = e.target as HTMLElement;
            if (isInteractiveTarget(target) || item.classList.contains('delete-pending')) return;
            clickCount++;
            if (clickCount === 1) {
                clickTimer = setTimeout(() => { clickCount = 0; }, 400);
            } else if (clickCount >= 2) {
                if (clickTimer !== null) clearTimeout(clickTimer);
                clickCount = 0;
                openEditShoppingModal(itemId);
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector<HTMLInputElement>('input[name="search"]');
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            (searchInput.closest('form') as HTMLFormElement | null)?.submit();
        }
    });

    initLongPressDelete();
    initShoppingDoubleClick();
});
