// メモ管理用JavaScript

// メモの展開/折りたたみ
function toggleMemoExpand(memoId) {
    const preview = document.getElementById(`preview-${memoId}`);
    const fullContent = document.getElementById(`full-content-${memoId}`);
    const icon = document.getElementById(`icon-${memoId}`);
    
    if (fullContent.style.display === 'none') {
        renderMemoContent(fullContent);
        preview.style.display = 'none';
        fullContent.style.display = 'block';
        icon.classList.add('expanded');
    } else {
        preview.style.display = 'block';
        fullContent.style.display = 'none';
        icon.classList.remove('expanded');
    }
}

let markdownEnabled = false;
let memoMdRenderer = null;

function renderMemoContent(fullContentEl) {
    if (!fullContentEl) return;
    let raw = '';
    if (fullContentEl.dataset.rawId) {
        const source = document.getElementById(fullContentEl.dataset.rawId);
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
        fullContentEl.innerHTML = fullContentEl.textContent.replace(/\n/g, '<br>');
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
        } else {
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
    fetch(`/carbohydratepro/memos/toggle-favorite/${memoId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // アイコンの更新
            const icon = button.querySelector('i');
            if (data.is_favorite) {
                icon.className = 'fas fa-star';
                button.setAttribute('data-favorite', 'true');
                button.setAttribute('title', 'お気に入り解除');
            } else {
                icon.className = 'far fa-star';
                button.setAttribute('data-favorite', 'false');
                button.setAttribute('title', 'お気に入り');
            }
            // ページをリロードしてソート順を更新
            setTimeout(() => location.reload(), 500);
        }
    })
    .catch(error => console.error('Error:', error));
}

// 編集モーダル関連
function openEditMemoModal(memoId) {
    $.ajax({
        url: '/carbohydratepro/memos/edit/' + memoId + '/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#editMemoModal .modal-dialog').html(response);
            $('#editMemoModal').modal('show');
            
            // フォーム送信時の処理
            $('#editMemoForm').on('submit', function(e) {
                e.preventDefault();
                $.ajax({
                    url: $(this).attr('action'),
                    type: 'POST',
                    data: $(this).serialize(),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    success: function(response) {
                        if (response.success) {
                            $('#editMemoModal').modal('hide');
                            location.reload();
                        } else {
                            alert('エラーが発生しました。入力内容を確認してください。');
                        }
                    },
                    error: function() {
                        alert('保存に失敗しました。');
                    }
                });
            });
        },
        error: function() {
            alert('データの読み込みに失敗しました。');
        }
    });
}

// 新規作成モーダル関連
function openCreateMemoModal() {
    $.ajax({
        url: '/carbohydratepro/memos/create/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#createMemoModal .modal-dialog').html(response);
            $('#createMemoModal').modal('show');
            
            // フォーム送信時の処理
            $('#createMemoForm').on('submit', function(e) {
                e.preventDefault();
                $.ajax({
                    url: $(this).attr('action'),
                    type: 'POST',
                    data: $(this).serialize(),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    success: function(response) {
                        if (response.success) {
                            $('#createMemoModal').modal('hide');
                            location.reload();
                        } else {
                            alert('エラーが発生しました。入力内容を確認してください。');
                        }
                    },
                    error: function() {
                        alert('保存に失敗しました。');
                    }
                });
            });
        },
        error: function() {
            alert('データの読み込みに失敗しました。');
        }
    });
}

// フィルター関連のイベント処理
function initializeMemoFilters() {
    var filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            this.submit();
        });
    }

    var memoTypeFilter = document.getElementById('memo_type_filter');
    if (memoTypeFilter) {
        memoTypeFilter.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    }
    
    var favoriteFilter = document.getElementById('favorite_filter');
    if (favoriteFilter) {
        favoriteFilter.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    }

    var searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('filterForm').submit();
            }
        });
    }
}

// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeMemoFilters();
    const saved = localStorage.getItem('memoMarkdownEnabled');
    setMarkdownMode(saved === '1');
});
