// タスク管理用JavaScript

// カレンダーセルのクリックイベント処理
function setupCalendarClickEvents() {
    // カレンダーセル全体のクリックイベント
    document.querySelectorAll('.task-calendar-cell[data-day]').forEach(function(cell) {
        cell.addEventListener('click', function(e) {
            const day = this.dataset.day;
            const month = this.dataset.month;
            const taskCount = parseInt(this.dataset.taskCount);
            const year = this.dataset.year;
            const monthNum = this.dataset.monthNum;
            
            // タスクアイテムをクリックした場合もタスク一覧を表示
            if (e.target.closest('.task-item')) {
                // タスクがある場合は必ず一覧表示
                if (taskCount > 0) {
                    showDayTasksModal(year, monthNum, day, month);
                }
                return;
            }
            
            // タスク以外の空白部分をクリックした場合
            if (taskCount > 0) {
                // タスクがある場合は一覧表示
                showDayTasksModal(year, monthNum, day, month);
            } else {
                // タスクがない場合は新規作成
                openCreateTaskModalWithDate(year, monthNum, day);
            }
        });
    });
}

// 日付のタスク一覧を表示するモーダル
function showDayTasksModal(year, month, day, monthLabel) {
    const modalTitle = `${monthLabel} ${day}日のタスク`;
    document.getElementById('dayTasksModalLabel').textContent = modalTitle;
    
    // 「この日にタスクを追加」ボタンのイベント設定
    const addTaskBtn = document.getElementById('addTaskForDayBtn');
    if (addTaskBtn) {
        // 既存のイベントリスナーを削除
        const newBtn = addTaskBtn.cloneNode(true);
        addTaskBtn.parentNode.replaceChild(newBtn, addTaskBtn);
        
        // 新しいイベントリスナーを追加
        newBtn.addEventListener('click', function() {
            $('#dayTasksModal').modal('hide');
            setTimeout(function() {
                openCreateTaskModalWithDate(year, month, day);
            }, 300);
        });
    }
    
    // その日のタスクを取得してAjaxで取得
    fetch(`/carbohydratepro/tasks/day/${year}-${month}-${day}/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('dayTasksModalBody');
            
            if (data.tasks && data.tasks.length > 0) {
                let html = '';
                data.tasks.forEach(task => {
                    const statusBadge = task.status === 'completed' ? 'badge-success' : 
                                       task.status === 'in_progress' ? 'badge-info' : 'badge-secondary';
                    const priorityBadge = task.priority === 'high' ? 'badge-danger' :
                                         task.priority === 'medium' ? 'badge-warning' : 'badge-secondary';
                    
                    // ラベルの色を適用
                    const borderStyle = task.label ? `style="border-left: 4px solid ${task.label.color};"` : '';
                    const labelHtml = task.label ? 
                        `<span class="badge mr-1" style="background-color: ${task.label.color}; color: white;">
                            <i class="fas fa-tag"></i> ${task.label.name}
                        </span>` : '';
                    
                    html += `
                        <div class="card task-card-mini mb-2" ${borderStyle}>
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="mb-0 flex-grow-1">${task.title}</h6>
                                    <div class="d-flex ml-2" style="white-space: nowrap;">
                                        <button onclick="openEditTaskModalFromList(${task.id})" class="btn btn-sm btn-outline-warning py-0 px-1 mr-1" title="編集">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button onclick="deleteTaskFromList(${task.id})" class="btn btn-sm btn-outline-danger py-0 px-1" title="削除">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                                ${task.due_date ? `<p class="small text-muted mb-2"><i class="far fa-clock"></i> ${task.due_date}</p>` : ''}
                                ${task.description ? `<p class="small text-muted mb-2">${task.description}</p>` : ''}
                                <div class="d-flex flex-wrap gap-1">
                                    ${labelHtml}
                                    <span class="badge ${priorityBadge} mr-1">${task.priority_display}</span>
                                    <span class="badge ${statusBadge}">${task.status_display}</span>
                                </div>
                            </div>
                        </div>
                    `;
                });
                modalBody.innerHTML = html;
            } else {
                modalBody.innerHTML = '<p class="text-center text-muted">この日のタスクはありません</p>';
            }
            
            $('#dayTasksModal').modal('show');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('タスクの取得に失敗しました。');
        });
}

// 一覧モーダルから編集モーダルを開く
function openEditTaskModalFromList(taskId) {
    // 一覧モーダルを閉じる
    $('#dayTasksModal').modal('hide');
    
    // 編集モーダルを開く
    setTimeout(function() {
        openEditTaskModal(taskId);
    }, 300); // モーダルのアニメーション完了を待つ
}

// 一覧モーダルからタスクを削除
function deleteTaskFromList(taskId) {
    if (!confirm('このタスクを削除してもよろしいですか？')) {
        return;
    }
    
    // CSRFトークンを取得
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    fetch(`/carbohydratepro/tasks/delete/${taskId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    })
    .then(response => {
        if (response.ok) {
            // モーダルを閉じてページをリロード
            $('#dayTasksModal').modal('hide');
            setTimeout(function() {
                location.reload();
            }, 300);
        } else {
            alert('削除に失敗しました。');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('削除に失敗しました。');
    });
}

// 指定日付で新規タスク作成モーダルを開く
function openCreateTaskModalWithDate(year, month, day) {
    const dueDate = `${year}-${month}-${day}T09:00`;
    
    $.ajax({
        url: '/carbohydratepro/tasks/create/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#createTaskModal .modal-dialog').html(response);
            
            // 期限日フィールドに日付を設定
            const dueDateField = document.getElementById('id_due_date');
            if (dueDateField) {
                dueDateField.value = dueDate;
            }
            
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

// 月選択フォームのイベント処理
function initializeMonthFilter() {
    var monthInput = document.getElementById('target_date');
    if (monthInput) {
        monthInput.addEventListener('change', function() {
            document.getElementById('monthFilterForm').submit();
        });
    }
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
    initializeMonthFilter();
    initializeTaskFilters();
    setupCalendarClickEvents();
});
