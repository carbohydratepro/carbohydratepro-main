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

// フィルター関連のイベント処理
function initializeTaskFilters() {
    // フィルター変更時とEnterキー押下時の処理
    var filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            this.submit();
        });
    }

    // セレクトボックス変更時に自動検索
    var statusFilter = document.getElementById('status_filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    }
    
    var priorityFilter = document.getElementById('priority_filter');
    if (priorityFilter) {
        priorityFilter.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    }

    // 検索フィールドでEnterキー押下時の処理
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
    initializeTaskFilters();
});
