// 取引管理用JavaScript

// 編集モーダル関連
function openEditModal(transactionId) {
    $.ajax({
        url: '/carbohydratepro/expenses/edit/' + transactionId + '/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#editModal .modal-dialog').html(response);
            $('#editModal').modal('show');
            
            // フォーム送信時の処理
            $('#editTransactionForm').on('submit', function(e) {
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
                            $('#editModal').modal('hide');
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
function openCreateModal(createUrl) {
    // createUrlが指定されていない場合はデフォルトのURLを使用
    if (!createUrl) {
        createUrl = '/carbohydratepro/expenses/create/';
    }
    
    $.ajax({
        url: createUrl,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#createModal .modal-dialog').html(response);
            $('#createModal').modal('show');
            
            // フォーム送信時の処理
            $('#createTransactionForm').on('submit', function(e) {
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
                            $('#createModal').modal('hide');
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

$(document).ready(function() {
    // 日付フィールドのdatepicker設定
    $('.datepicker').on('click', function() {
        this.showPicker();
    });
    
    // 金額フィールドの整数入力制限
    $('input[name="amount"]').on('input', function() {
        // 小数点が入力された場合は削除
        this.value = this.value.replace(/[^\d]/g, '');
    });
    
    // 金額フィールドのペースト時の処理
    $('input[name="amount"]').on('paste', function(e) {
        setTimeout(function() {
            var input = e.target;
            input.value = input.value.replace(/[^\d]/g, '');
        }, 1);
    });
});