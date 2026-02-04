// タスク管理用JavaScript

// 表示モード切替関数
function switchViewMode(mode) {
    const currentUrl = new URL(window.location.href);
    const targetDate = currentUrl.searchParams.get('target_date');

    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set('view_mode', mode);

    if (mode === 'day') {
        const dateStr = new Date().toISOString().split('T')[0];
        newUrl.searchParams.set('target_date', dateStr);
    } else {
        if (targetDate?.match(/^\d{4}-\d{2}-\d{2}$/)) {
            newUrl.searchParams.set('target_date', targetDate.substring(0, 7));
        } else if (targetDate?.match(/^\d{4}-\d{2}$/)) {
            newUrl.searchParams.set('target_date', targetDate);
        } else {
            newUrl.searchParams.set('target_date', new Date().toISOString().substring(0, 7));
        }
    }

    window.location.href = newUrl.toString();
}

// テキストを指定文字数で切り詰める関数
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length <= maxLength ? text : text.substring(0, maxLength) + '...';
}

// カレンダーセルのクリックイベント処理
function setupCalendarClickEvents() {
    document.querySelectorAll('.task-calendar-cell[data-day]').forEach(cell => {
        cell.addEventListener('click', (e) => {
            const { day, month, taskCount, year, monthNum } = cell.dataset;
            const count = parseInt(taskCount);

            if (e.target.closest('.task-item')) {
                if (count > 0) showDayTasksModal(year, monthNum, day, month);
                return;
            }

            if (count > 0) {
                showDayTasksModal(year, monthNum, day, month);
            } else {
                openCreateTaskModalWithDate(year, monthNum, day);
            }
        });
    });
}

// 日付のタスク一覧を表示するモーダル
function showDayTasksModal(year, month, day, monthLabel) {
    const paddedMonth = String(month).padStart(2, '0');
    const paddedDay = String(day).padStart(2, '0');
    const modalTitle = `${year}/${paddedMonth}/${paddedDay}`;
    document.getElementById('dayTasksModalLabel').textContent = modalTitle;

    const modal = document.getElementById('dayTasksModal');
    modal.dataset.year = year;
    modal.dataset.month = paddedMonth;
    modal.dataset.day = paddedDay;

    // 「この日にタスクを追加」ボタンのイベント設定
    const addTaskBtn = document.getElementById('addTaskForDayBtn');
    if (addTaskBtn) {
        const newBtn = addTaskBtn.cloneNode(true);
        addTaskBtn.parentNode.replaceChild(newBtn, addTaskBtn);
        newBtn.addEventListener('click', () => {
            $('#dayTasksModal').modal('hide');
            setTimeout(() => openCreateTaskModalWithDate(year, month, day), 300);
        });
    }

    // 「ガントチャートで表示」ボタンのイベント設定
    const ganttViewBtn = document.getElementById('viewGanttForDayBtn');
    if (ganttViewBtn) {
        const newGanttBtn = ganttViewBtn.cloneNode(true);
        ganttViewBtn.parentNode.replaceChild(newGanttBtn, ganttViewBtn);
        newGanttBtn.addEventListener('click', () => {
            window.location.href = `?view_mode=day&target_date=${year}-${paddedMonth}-${paddedDay}`;
        });
    }

    // その日のタスクをfetchで取得
    fetch(`/carbohydratepro/tasks/day/${year}-${month}-${day}/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('dayTasksModalBody');

            if (data.tasks?.length > 0) {
                modalBody.innerHTML = data.tasks.map(task => {
                    const statusBadge = task.status === 'completed' ? 'badge-success' :
                                       task.status === 'in_progress' ? 'badge-info' : 'badge-secondary';
                    const priorityBadge = task.priority === 'high' ? 'badge-danger' :
                                         task.priority === 'medium' ? 'badge-warning' : 'badge-secondary';
                    const borderStyle = task.label ? `style="border-left: 4px solid ${task.label.color};"` : '';
                    const labelHtml = task.label ?
                        `<span class="badge mr-1" style="background-color: ${task.label.color}; color: white;">
                            <i class="fas fa-tag"></i> ${task.label.name}
                        </span>` : '';

                    return `
                        <div class="card task-card-mini mb-2" ${borderStyle}>
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="mb-0 flex-grow-1">${truncateText(task.title, 30)}</h6>
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
                }).join('');
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
    $('#dayTasksModal').modal('hide');
    setTimeout(() => openEditTaskModal(taskId), 300);
}

// 一覧モーダルからタスクを削除
function deleteTaskFromList(taskId) {
    if (!confirm('このタスクを削除してもよろしいですか？')) return;

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
            $('#dayTasksModal').modal('hide');
            setTimeout(() => location.reload(), 300);
        } else {
            alert('削除に失敗しました。');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('削除に失敗しました。');
    });
}

// フォームデータをURLSearchParams形式に変換
function serializeTaskForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}

// タスクモーダルフォーム送信の共通処理
async function submitTaskModalForm(form, modalSelector) {
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: serializeTaskForm(form),
        });
        const data = await response.json();
        if (data.success) {
            $(modalSelector).modal('hide');
            location.reload();
        } else {
            alert('エラーが発生しました。入力内容を確認してください。');
        }
    } catch {
        alert('保存に失敗しました。');
    }
}

// 指定日付で新規タスク作成モーダルを開く
async function openCreateTaskModalWithDate(year, month, day) {
    const selectedDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    try {
        const response = await fetch('/carbohydratepro/tasks/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#createTaskModal .modal-dialog').innerHTML = html;

        const startDateField = document.getElementById('id_start_date');
        const endDateField = document.getElementById('id_end_date');
        if (startDateField) startDateField.value = selectedDate;
        if (endDateField) endDateField.value = selectedDate;

        $('#createTaskModal').modal('show');
        initializeTaskFormControls();

        const form = document.getElementById('createTaskForm');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            submitTaskModalForm(form, '#createTaskModal');
        });
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 編集モーダル関連
async function openEditTaskModal(taskId) {
    try {
        const response = await fetch(`/carbohydratepro/tasks/edit/${taskId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#editTaskModal .modal-dialog').innerHTML = html;
        $('#editTaskModal').modal('show');
        initializeTaskFormControls();

        const form = document.getElementById('editTaskForm');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            submitTaskModalForm(form, '#editTaskModal');
        });
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 新規作成モーダル関連
async function openCreateTaskModal() {
    try {
        const response = await fetch('/carbohydratepro/tasks/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#createTaskModal .modal-dialog').innerHTML = html;
        $('#createTaskModal').modal('show');
        initializeTaskFormControls();

        const form = document.getElementById('createTaskForm');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            submitTaskModalForm(form, '#createTaskModal');
        });
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 月選択フォームのイベント処理
function initializeMonthFilter() {
    const monthInput = document.getElementById('target_date');
    monthInput?.addEventListener('change', () => {
        document.getElementById('monthFilterForm').submit();
    });
}

// フィルター関連のイベント処理
function initializeTaskFilters() {
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            filterForm.submit();
        });
    }

    const statusFilter = document.getElementById('status_filter');
    statusFilter?.addEventListener('change', () => {
        document.getElementById('filterForm').submit();
    });

    const priorityFilter = document.getElementById('priority_filter');
    priorityFilter?.addEventListener('change', () => {
        document.getElementById('filterForm').submit();
    });

    const searchInput = document.getElementById('search');
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('filterForm').submit();
        }
    });
}

// ページ読み込み時にフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeMonthFilter();
    initializeTaskFilters();
    setupCalendarClickEvents();
    initializeTaskFormControls();
    initializeGanttScroll();
});

// ガントチャートの初期スクロール位置を設定
function initializeGanttScroll() {
    const ganttContainer = document.getElementById('ganttContainer');
    if (!ganttContainer) return;

    const now = new Date();
    const scrollPosition = (now.getHours() * 100) + (now.getMinutes() * 100 / 60);
    const containerWidth = ganttContainer.clientWidth;
    ganttContainer.scrollLeft = Math.max(0, scrollPosition - (containerWidth / 2));
}

// タスクフォーム制御の初期化
function initializeTaskFormControls() {
    const allDayCheckbox = document.querySelector('#id_all_day');
    if (allDayCheckbox) {
        toggleTimeFields();
        allDayCheckbox.addEventListener('change', toggleTimeFields);
    }

    const frequencySelect = document.querySelector('#id_frequency');
    if (frequencySelect) {
        toggleRepeatFields();
        frequencySelect.addEventListener('change', toggleRepeatFields);
    }
}

// 時間フィールドの表示/非表示を切り替え
function toggleTimeFields() {
    const allDayCheckbox = document.querySelector('#id_all_day');
    const timeFields = document.querySelectorAll('.time-field');

    if (allDayCheckbox && timeFields.length > 0) {
        const isAllDay = allDayCheckbox.checked;
        timeFields.forEach(field => {
            field.style.display = isAllDay ? 'none' : 'block';
            if (isAllDay) {
                const input = field.querySelector('input[type="time"]');
                if (input) input.value = '';
            }
        });
    }
}

// 繰り返し設定フィールドの表示/非表示を切り替え
function toggleRepeatFields() {
    const frequencySelect = document.querySelector('#id_frequency');
    const repeatFields = document.querySelectorAll('.repeat-field');

    if (frequencySelect && repeatFields.length > 0) {
        const hasFrequency = frequencySelect.value && frequencySelect.value !== '';
        repeatFields.forEach(field => {
            field.style.display = hasFrequency ? 'block' : 'none';
        });
    }
}
