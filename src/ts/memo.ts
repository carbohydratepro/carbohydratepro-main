// メモ管理用JavaScript

interface MarkdownRenderer {
  render: (text: string) => string;
}

interface MemoModalResponse {
  success: boolean;
}

// メモの展開/折りたたみ
function toggleMemoExpand(memoId: string): void {
    const preview = document.getElementById(`preview-${memoId}`);
    const fullContent = document.getElementById(`full-content-${memoId}`);
    const icon = document.getElementById(`icon-${memoId}`);

    if (!fullContent) return;

    if (fullContent.style.display === 'none') {
        renderMemoContent(fullContent);
        if (preview) preview.style.display = 'none';
        fullContent.style.display = 'block';
        if (icon) icon.classList.add('expanded');
    } else {
        if (preview) preview.style.display = 'block';
        fullContent.style.display = 'none';
        if (icon) icon.classList.remove('expanded');
    }
}

let markdownEnabled = false;
let memoMdRenderer: MarkdownRenderer | null = null;

function renderMemoContent(fullContentEl: HTMLElement): void {
    if (!fullContentEl) return;
    let raw = '';
    if (fullContentEl.dataset.rawId) {
        const source = document.getElementById(fullContentEl.dataset.rawId) as HTMLInputElement | null;
        raw = source ? source.value : '';
    } else if (fullContentEl.dataset.raw) {
        raw = decodeURIComponent(fullContentEl.dataset.raw);
    }
    if (markdownEnabled) {
        if (!memoMdRenderer) {
            if (window.markdownit) {
                memoMdRenderer = window.markdownit({ html: false, linkify: true, breaks: true });
            } else if (window.memoMarkdownRender) {
                memoMdRenderer = { render: window.memoMarkdownRender };
            }
        }
        const rendered = memoMdRenderer ? memoMdRenderer.render(raw) : raw;
        fullContentEl.innerHTML = rendered;
    } else {
        fullContentEl.textContent = raw;
        fullContentEl.innerHTML = (fullContentEl.textContent ?? '').replace(/\n/g, '<br>');
    }
}

function setMarkdownMode(enabled: boolean): void {
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
        } else {
            offBtn.classList.add('btn-primary');
            offBtn.classList.remove('btn-outline-secondary');
            onBtn.classList.add('btn-outline-secondary');
            onBtn.classList.remove('btn-primary');
        }
    }
    document.querySelectorAll<HTMLElement>('.memo-full-content').forEach(el => {
        if (el.style.display !== 'none') {
            renderMemoContent(el);
        }
    });
}

// お気に入りの切り替え
function toggleFavorite(memoId: string, button: HTMLElement): void {
    fetch(`/carbohydratepro/memos/toggle-favorite/${memoId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value || '',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const icon = button.querySelector('i');
            if (data.is_favorite) {
                if (icon) icon.className = 'fas fa-star';
                button.setAttribute('data-favorite', 'true');
                button.setAttribute('title', 'お気に入り解除');
            } else {
                if (icon) icon.className = 'far fa-star';
                button.setAttribute('data-favorite', 'false');
                button.setAttribute('title', 'お気に入り');
            }
            setTimeout(() => location.reload(), 500);
        }
    })
    .catch(error => console.error('Error:', error));
}

// フォームデータをURLSearchParams形式に変換
function serializeMemoForm(form: HTMLFormElement): string {
    return new URLSearchParams(new FormData(form) as unknown as Record<string, string>).toString();
}

// 編集モーダル関連
async function openEditMemoModal(memoId: string): Promise<void> {
    try {
        const response = await fetch(`/carbohydratepro/memos/edit/${memoId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#editMemoModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
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
                    const data: MemoModalResponse = await res.json();
                    if (data.success) {
                        $('#editMemoModal').modal('hide');
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
async function openCreateMemoModal(): Promise<void> {
    try {
        const response = await fetch('/carbohydratepro/memos/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#createMemoModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
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
                    const data: MemoModalResponse = await res.json();
                    if (data.success) {
                        $('#createMemoModal').modal('hide');
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
function initializeMemoFilters(): void {
    const filterForm = document.getElementById('filterForm') as HTMLFormElement | null;
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            filterForm.submit();
        });
    }

    const memoTypeFilter = document.getElementById('memo_type_filter');
    memoTypeFilter?.addEventListener('change', () => {
        (document.getElementById('filterForm') as HTMLFormElement | null)?.submit();
    });

    const favoriteFilter = document.getElementById('favorite_filter');
    favoriteFilter?.addEventListener('change', () => {
        (document.getElementById('filterForm') as HTMLFormElement | null)?.submit();
    });

    const searchInput = document.getElementById('search');
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            (document.getElementById('filterForm') as HTMLFormElement | null)?.submit();
        }
    });
}

// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeMemoFilters();
    const saved = localStorage.getItem('memoMarkdownEnabled');
    setMarkdownMode(saved === '1');
});
