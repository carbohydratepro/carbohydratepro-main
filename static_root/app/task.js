// タスク管理用JavaScript

// 編集モーダル関連
function openEditTaskModal(taskId) {
    $.ajax({
        url: '/carbohydratepro/tasks/edit/' + taskId + '/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#editTaskModal .modal-dialog').html(response);
            $('#editTaskModal').modal('show');
            
            // フォーム送信時の処理
            $('#editTaskForm').on('submit', function(e) {
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
                            $('#editTaskModal').modal('hide');
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
function openCreateTaskModal() {
    $.ajax({
        url: '/carbohydratepro/tasks/create/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#createTaskModal .modal-dialog').html(response);
            $('#createTaskModal').modal('show');
            
            // フォーム送信時の処理
            $('#createTaskForm').on('submit', function(e) {
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
                            $('#createTaskModal').modal('hide');
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
