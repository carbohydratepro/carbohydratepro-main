// 買い物リスト管理用JavaScript

// 残数の更新
function updateCount(itemId, action) {
    fetch(`/carbohydratepro/shopping/update-count/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `action=${action}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`count-${itemId}`).textContent = data.remaining_count;
            
            // ステータスバッジの更新
            const card = document.querySelector(`#count-${itemId}`).closest('.shopping-item-card');
            const badge = card.querySelector('.badge');
            
            if (data.status_code === 'insufficient') {
                badge.className = 'badge badge-danger';
                card.className = card.className.replace('border-success', 'border-danger');
            } else {
                badge.className = 'badge badge-success';
                card.className = card.className.replace('border-danger', 'border-success');
            }
            badge.textContent = data.status;
            
            // 不足の場合は上位に移動するため、少し待ってからページをリロード
            if (action === 'decrease' && data.remaining_count === 0) {
                setTimeout(() => location.reload(), 500);
            }
        }
    })
    .catch(error => console.error('Error:', error));
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
