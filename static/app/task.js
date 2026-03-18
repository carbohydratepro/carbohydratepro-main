"use strict";
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
    }
    else {
        if (targetDate === null || targetDate === void 0 ? void 0 : targetDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
            newUrl.searchParams.set('target_date', targetDate.substring(0, 7));
        }
        else if (targetDate === null || targetDate === void 0 ? void 0 : targetDate.match(/^\d{4}-\d{2}$/)) {
            newUrl.searchParams.set('target_date', targetDate);
        }
        else {
            newUrl.searchParams.set('target_date', new Date().toISOString().substring(0, 7));
        }
    }
    window.location.href = newUrl.toString();
}
// テキストを指定文字数で切り詰める関数
function truncateText(text, maxLength) {
    if (!text)
        return '';
    return text.length <= maxLength ? text : text.substring(0, maxLength) + '...';
}
// カレンダーセルのクリックイベント処理
function setupCalendarClickEvents() {
    document.querySelectorAll('.task-calendar-cell[data-day]').forEach(cell => {
        cell.addEventListener('click', (e) => {
            const { day, month, taskCount, year, monthNum } = cell.dataset;
            const count = parseInt(taskCount !== null && taskCount !== void 0 ? taskCount : '0');
            if (e.target.closest('.task-item')) {
                if (count > 0)
                    showDayTasksModal(year, monthNum, day, month);
                return;
            }
            if (count > 0) {
                showDayTasksModal(year, monthNum, day, month);
            }
            else {
                openCreateTaskModalWithDate(year, monthNum, day);
            }
        });
    });
}
// 日付のタスク一覧を表示するモーダル
function showDayTasksModal(year, month, day, monthLabel) {
    var _a, _b;
    const paddedMonth = String(month).padStart(2, '0');
    const paddedDay = String(day).padStart(2, '0');
    const modalTitle = `${year}/${paddedMonth}/${paddedDay}`;
    const modalLabel = document.getElementById('dayTasksModalLabel');
    if (modalLabel)
        modalLabel.textContent = modalTitle;
    const modal = document.getElementById('dayTasksModal');
    if (modal) {
        modal.dataset.year = year;
        modal.dataset.month = paddedMonth;
        modal.dataset.day = paddedDay;
    }
    // 「この日にタスクを追加」ボタンのイベント設定
    const addTaskBtn = document.getElementById('addTaskForDayBtn');
    if (addTaskBtn) {
        const newBtn = addTaskBtn.cloneNode(true);
        (_a = addTaskBtn.parentNode) === null || _a === void 0 ? void 0 : _a.replaceChild(newBtn, addTaskBtn);
        newBtn.addEventListener('click', () => {
            $('#dayTasksModal').modal('hide');
            setTimeout(() => openCreateTaskModalWithDate(year, month, day), 300);
        });
    }
    // 「ガントチャートで表示」ボタンのイベント設定
    const ganttViewBtn = document.getElementById('viewGanttForDayBtn');
    if (ganttViewBtn) {
        const newGanttBtn = ganttViewBtn.cloneNode(true);
        (_b = ganttViewBtn.parentNode) === null || _b === void 0 ? void 0 : _b.replaceChild(newGanttBtn, ganttViewBtn);
        newGanttBtn.addEventListener('click', () => {
            window.location.href = `?view_mode=day&target_date=${year}-${paddedMonth}-${paddedDay}`;
        });
    }
    // その日のタスクをfetchで取得
    fetch(`/carbohydratepro/tasks/day/${year}-${month}-${day}/`)
        .then(response => response.json())
        .then((data) => {
        var _a;
        const modalBody = document.getElementById('dayTasksModalBody');
        if (!modalBody)
            return;
        if (((_a = data.tasks) === null || _a === void 0 ? void 0 : _a.length) > 0) {
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
                        <div class="card task-card-mini mb-2 lp-delete-item"
                             data-delete-url="/carbohydratepro/tasks/delete/${task.id}/"
                             data-item-id="${task.id}"
                             ${borderStyle}>
                            <div class="lp-delete-overlay"><i class="fas fa-trash-alt"></i> 削除</div>
                            <div class="card-body">
                                <h6 class="mb-1">${truncateText(task.title, 30)}</h6>
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
            initLongPressDelete(modalBody);
            modalBody.querySelectorAll('.task-card-mini').forEach(card => {
                var _a;
                let lastTapTime = 0;
                let suppressClick = false;
                let clickCount = 0;
                let clickTimer = null;
                const taskId = parseInt((_a = card.dataset['itemId']) !== null && _a !== void 0 ? _a : '0', 10);
                card.addEventListener('touchend', (e) => {
                    const el = e.target;
                    if (isInteractiveTarget(el) || !!el.closest('.lp-delete-overlay') || card.classList.contains('delete-pending'))
                        return;
                    const now = Date.now();
                    if (now - lastTapTime < 400) {
                        e.preventDefault();
                        suppressClick = true;
                        lastTapTime = 0;
                        if (taskId)
                            openEditTaskModalFromList(taskId);
                    }
                    else {
                        lastTapTime = now;
                    }
                }, { passive: false });
                card.addEventListener('click', (e) => {
                    if (suppressClick) {
                        suppressClick = false;
                        return;
                    }
                    const el = e.target;
                    if (isInteractiveTarget(el) || !!el.closest('.lp-delete-overlay') || card.classList.contains('delete-pending'))
                        return;
                    clickCount++;
                    if (clickCount === 1) {
                        clickTimer = setTimeout(() => { clickCount = 0; }, 400);
                    }
                    else if (clickCount >= 2) {
                        if (clickTimer !== null)
                            clearTimeout(clickTimer);
                        clickCount = 0;
                        if (taskId)
                            openEditTaskModalFromList(taskId);
                    }
                });
            });
        }
        else {
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
    var _a;
    if (!confirm('このタスクを削除してもよろしいですか？'))
        return;
    const csrfToken = ((_a = document.querySelector('[name=csrfmiddlewaretoken]')) === null || _a === void 0 ? void 0 : _a.value) || '';
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
        }
        else {
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
// フォームのエラーメッセージを表示する
function displayTaskFormErrors(form, errors) {
    // 既存の動的エラーメッセージをクリア
    form.querySelectorAll('.dynamic-form-error').forEach(el => el.remove());
    const nonFieldErrors = [];
    for (const [field, messages] of Object.entries(errors)) {
        if (field === '__all__') {
            nonFieldErrors.push(...messages);
        }
        else {
            // フィールド固有のエラーをフィールドの隣に表示
            const fieldEl = form.querySelector(`[name="${field}"], #id_${field}`);
            if (fieldEl === null || fieldEl === void 0 ? void 0 : fieldEl.parentNode) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-danger small dynamic-form-error mt-1';
                errorDiv.textContent = messages.join(' / ');
                fieldEl.parentNode.appendChild(errorDiv);
            }
            else {
                nonFieldErrors.push(...messages);
            }
        }
    }
    if (nonFieldErrors.length > 0) {
        const modalBody = form.querySelector('.modal-body');
        if (modalBody) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger dynamic-form-error';
            alertDiv.innerHTML = nonFieldErrors.map(e => `<div>${e}</div>`).join('');
            modalBody.prepend(alertDiv);
        }
    }
}
// タスクモーダルフォーム送信の共通処理
async function submitTaskModalForm(form, modalSelector) {
    var _a;
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
        }
        else {
            displayTaskFormErrors(form, (_a = data.errors) !== null && _a !== void 0 ? _a : {});
        }
    }
    catch (_b) {
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
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#createTaskModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        const startDateField = document.getElementById('id_start_date');
        const endDateField = document.getElementById('id_end_date');
        if (startDateField)
            startDateField.value = selectedDate;
        if (endDateField)
            endDateField.value = selectedDate;
        $('#createTaskModal').modal('show');
        initializeTaskFormControls();
        const form = document.getElementById('createTaskForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitTaskModalForm(form, '#createTaskModal');
            });
        }
    }
    catch (_a) {
        alert('データの読み込みに失敗しました。');
    }
}
// 編集モーダル関連
async function openEditTaskModal(taskId) {
    try {
        const response = await fetch(`/carbohydratepro/tasks/edit/${taskId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#editTaskModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#editTaskModal').modal('show');
        initializeTaskFormControls();
        const form = document.getElementById('editTaskForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitTaskModalForm(form, '#editTaskModal');
            });
        }
    }
    catch (_a) {
        alert('データの読み込みに失敗しました。');
    }
}
// 新規作成モーダル関連
async function openCreateTaskModal() {
    try {
        const response = await fetch('/carbohydratepro/tasks/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#createTaskModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#createTaskModal').modal('show');
        initializeTaskFormControls();
        const form = document.getElementById('createTaskForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitTaskModalForm(form, '#createTaskModal');
            });
        }
    }
    catch (_a) {
        alert('データの読み込みに失敗しました。');
    }
}
// 月選択フォームのイベント処理
function initializeMonthFilter() {
    const monthInput = document.getElementById('target_date');
    monthInput === null || monthInput === void 0 ? void 0 : monthInput.addEventListener('change', () => {
        var _a;
        (_a = document.getElementById('monthFilterForm')) === null || _a === void 0 ? void 0 : _a.submit();
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
    statusFilter === null || statusFilter === void 0 ? void 0 : statusFilter.addEventListener('change', () => {
        var _a;
        (_a = document.getElementById('filterForm')) === null || _a === void 0 ? void 0 : _a.submit();
    });
    const priorityFilter = document.getElementById('priority_filter');
    priorityFilter === null || priorityFilter === void 0 ? void 0 : priorityFilter.addEventListener('change', () => {
        var _a;
        (_a = document.getElementById('filterForm')) === null || _a === void 0 ? void 0 : _a.submit();
    });
    const searchInput = document.getElementById('search');
    searchInput === null || searchInput === void 0 ? void 0 : searchInput.addEventListener('keypress', (e) => {
        var _a;
        if (e.key === 'Enter') {
            e.preventDefault();
            (_a = document.getElementById('filterForm')) === null || _a === void 0 ? void 0 : _a.submit();
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
    if (!ganttContainer)
        return;
    const now = new Date();
    const scrollPosition = (now.getHours() * 100) + (now.getMinutes() * 100 / 60);
    const containerWidth = ganttContainer.clientWidth;
    ganttContainer.scrollLeft = Math.max(0, scrollPosition - (containerWidth / 2));
}
// 時刻を5分刻みで丸める
function roundToNearest5Minutes(date) {
    const ms = 5 * 60 * 1000;
    return new Date(Math.round(date.getTime() / ms) * ms);
}
// 時刻をHH:MM形式にフォーマット
function formatTimeHHMM(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}
// 時刻フィールドをセレクトボックス（5分刻み）に置き換える
function initializeTimeSelects() {
    ['id_start_time', 'id_end_time'].forEach(inputId => {
        const inputEl = document.getElementById(inputId);
        if (!inputEl || inputEl.tagName === 'SELECT')
            return;
        const input = inputEl;
        const select = document.createElement('select');
        select.id = input.id;
        select.name = input.name;
        select.className = input.className;
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '-- 時刻を選択 --';
        select.appendChild(emptyOption);
        for (let hour = 0; hour < 24; hour++) {
            for (let minute = 0; minute < 60; minute += 5) {
                const option = document.createElement('option');
                const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
                option.value = timeStr;
                option.textContent = timeStr;
                select.appendChild(option);
            }
        }
        if (input.value) {
            select.value = input.value;
        }
        input.replaceWith(select);
    });
}
// デフォルト時刻を設定（新規作成時のみ：値が空の場合）
function setDefaultTimes() {
    const startTimeEl = document.getElementById('id_start_time');
    const endTimeEl = document.getElementById('id_end_time');
    if (!startTimeEl || !endTimeEl)
        return;
    const startTimeInput = startTimeEl;
    const endTimeInput = endTimeEl;
    if (startTimeInput.value || endTimeInput.value)
        return;
    const now = new Date();
    const rounded = roundToNearest5Minutes(now);
    const oneHourLater = new Date(rounded.getTime() + 60 * 60 * 1000);
    startTimeInput.value = formatTimeHHMM(rounded);
    endTimeInput.value = formatTimeHHMM(oneHourLater);
}
// 開始日変更時のイベント処理（終了日を同じ幅で移動・終了日ピッカーを自動オープン）
function handleStartDateChange(event) {
    var _a, _b, _c;
    const startDateInput = event.target;
    const form = startDateInput.closest('form');
    if (!form)
        return;
    const endDateInput = form.querySelector('#id_end_date');
    if (!endDateInput)
        return;
    const previousStartDateStr = (_a = startDateInput.dataset.previousValue) !== null && _a !== void 0 ? _a : '';
    const currentStartDateStr = startDateInput.value;
    if (!currentStartDateStr) {
        startDateInput.dataset.previousValue = '';
        return;
    }
    if (previousStartDateStr && endDateInput.value) {
        // 同じ幅を保ったまま終了日を更新
        const prevStart = new Date(previousStartDateStr);
        const prevEnd = new Date(endDateInput.value);
        if (!isNaN(prevStart.getTime()) && !isNaN(prevEnd.getTime())) {
            const diffMs = prevEnd.getTime() - prevStart.getTime();
            const newStart = new Date(currentStartDateStr);
            const newEnd = new Date(newStart.getTime() + diffMs);
            endDateInput.value = newEnd.toISOString().split('T')[0];
        }
    }
    else if (!endDateInput.value) {
        endDateInput.value = currentStartDateStr;
    }
    startDateInput.dataset.previousValue = currentStartDateStr;
    // 終了日ピッカーを自動で開く
    try {
        (_c = (_b = endDateInput).showPicker) === null || _c === void 0 ? void 0 : _c.call(_b);
    }
    catch (_d) {
        endDateInput.focus();
    }
    validateAndFixDateTimeOrder(form);
}
// 開始日時 > 終了日時の場合に自動修正する
function validateAndFixDateTimeOrder(form) {
    var _a, _b, _c;
    const startDateInput = form.querySelector('#id_start_date');
    const endDateInput = form.querySelector('#id_end_date');
    const startTimeEl = form.querySelector('#id_start_time');
    const endTimeEl = form.querySelector('#id_end_time');
    const allDayCheckbox = form.querySelector('#id_all_day');
    if (!startDateInput || !endDateInput)
        return;
    const startDateStr = startDateInput.value;
    const endDateStr = endDateInput.value;
    if (!startDateStr || !endDateStr)
        return;
    const isAllDay = (_a = allDayCheckbox === null || allDayCheckbox === void 0 ? void 0 : allDayCheckbox.checked) !== null && _a !== void 0 ? _a : false;
    const startTimeStr = isAllDay ? '00:00' : ((_b = startTimeEl === null || startTimeEl === void 0 ? void 0 : startTimeEl.value) !== null && _b !== void 0 ? _b : '');
    const endTimeStr = isAllDay ? '23:59' : ((_c = endTimeEl === null || endTimeEl === void 0 ? void 0 : endTimeEl.value) !== null && _c !== void 0 ? _c : '');
    if (!isAllDay && (!startTimeStr || !endTimeStr))
        return;
    const startDatetime = new Date(`${startDateStr}T${startTimeStr}:00`);
    const endDatetime = new Date(`${endDateStr}T${endTimeStr}:00`);
    if (isNaN(startDatetime.getTime()) || isNaN(endDatetime.getTime()))
        return;
    if (startDatetime > endDatetime) {
        // 終了日を開始日に合わせる
        endDateInput.value = startDateStr;
        if (!isAllDay && startTimeEl && endTimeEl) {
            // 終了時刻を開始時刻の1時間後に設定
            const parts = startTimeStr.split(':');
            const startHour = parseInt(parts[0]);
            const startMinute = parseInt(parts[1]);
            const endHour = startHour + 1;
            if (endHour >= 24) {
                endTimeEl.value = '23:55';
            }
            else {
                endTimeEl.value = `${String(endHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
            }
        }
    }
}
// タスクフォーム制御の初期化
function initializeTaskFormControls() {
    // 時刻フィールドをセレクトボックスに変換（他の処理より先に行う）
    initializeTimeSelects();
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
    // デフォルト時刻を設定（新規作成時のみ）
    setDefaultTimes();
    // 開始日変更イベントを設定
    const startDateInput = document.querySelector('#id_start_date');
    if (startDateInput) {
        startDateInput.dataset.previousValue = startDateInput.value;
        startDateInput.addEventListener('change', handleStartDateChange);
    }
    // 日時の整合性チェックイベントを設定
    const form = document.querySelector('#createTaskForm, #editTaskForm');
    if (form) {
        ['#id_end_date', '#id_start_time', '#id_end_time'].forEach(selector => {
            var _a;
            (_a = form.querySelector(selector)) === null || _a === void 0 ? void 0 : _a.addEventListener('change', () => {
                validateAndFixDateTimeOrder(form);
            });
        });
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
                const timeControl = field.querySelector('input[type="time"], select');
                if (timeControl)
                    timeControl.value = '';
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
