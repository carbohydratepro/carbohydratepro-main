// 買い物リスト管理用JavaScript

// 残数・不足数の更新（+/-/+10/-10ボタン用）
function updateCount(itemId, fieldType, action) {
    fetch(`/carbohydratepro/shopping/update-count/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `field_type=${fieldType}&action=${action}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 残数と不足数の表示を更新
            document.getElementById(`remaining-count-${itemId}`).textContent = data.remaining_count;
            document.getElementById(`threshold-count-${itemId}`).textContent = data.threshold_count;
            
            // カードの枠線の色を更新
            updateCardBorder(itemId, data.remaining_count, data.threshold_count);
        }
    })
    .catch(error => console.error('Error:', error));
}

// カードの枠線の色を更新する共通関数
function updateCardBorder(itemId, remainingCount, thresholdCount) {
    const card = document.querySelector(`#remaining-count-${itemId}`).closest('.shopping-item-card');
    
    // 既存の枠線クラスを削除
    card.classList.remove('border-success', 'border-danger');
    
    // 枠線の色を設定
    if (thresholdCount >= 1) {
        // 不足数が1以上の場合: 赤
        card.classList.add('border-danger');
    } else if (thresholdCount === 0 && remainingCount >= 1) {
        // 不足数が0かつ残数が1以上の場合: 緑
        card.classList.add('border-success');
    }
    // どちらもゼロの場合: 通常（クラスなし）
}

// 編集モーダル関連
function openEditShoppingModal(itemId) {
    $.ajax({
        url: '/carbohydratepro/shopping/edit/' + itemId + '/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#editShoppingModal .modal-dialog').html(response);
            $('#editShoppingModal').modal('show');
            
            // フォーム送信時の処理
            $('#editShoppingItemForm').on('submit', function(e) {
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
                            $('#editShoppingModal').modal('hide');
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
function openCreateShoppingModal() {
    $.ajax({
        url: '/carbohydratepro/shopping/create/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#createShoppingModal .modal-dialog').html(response);
            $('#createShoppingModal').modal('show');
            
            // フォーム送信時の処理
            $('#createShoppingItemForm').on('submit', function(e) {
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
                            $('#createShoppingModal').modal('hide');
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
function initializeShoppingFilters() {
    // 検索フォームの処理
    var searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            this.submit();
        });
    }

    var searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('searchForm').submit();
            }
        });
    }
}

// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeShoppingFilters();
});
