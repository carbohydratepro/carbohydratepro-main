// タスク管理用JavaScript

interface TaskLabelData {
  color: string;
  name: string;
}

interface TaskApiData {
  id: number;
  title: string;
  status: string;
  priority: string;
  status_display: string;
  priority_display: string;
  due_date: string | null;
  description: string | null;
  label: TaskLabelData | null;
}

interface TaskApiResponse {
  tasks: TaskApiData[];
}

interface TaskModalResponse {
  success: boolean;
  errors?: Record<string, string[]>;
}

// 表示モード切替関数
function switchViewMode(mode: string): void {
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
function truncateText(text: string, maxLength: number): string {
    if (!text) return '';
    return text.length <= maxLength ? text : text.substring(0, maxLength) + '...';
}

// カレンダーセルのクリックイベント処理
function setupCalendarClickEvents(): void {
    document.querySelectorAll<HTMLElement>('.task-calendar-cell[data-day]').forEach(cell => {
        cell.addEventListener('click', (e) => {
            const { day, month, taskCount, year, monthNum } = cell.dataset;
            const count = parseInt(taskCount ?? '0');

            if ((e.target as Element).closest('.task-item')) {
                if (count > 0) showDayTasksModal(year!, monthNum!, day!, month!);
                return;
            }

            if (count > 0) {
                showDayTasksModal(year!, monthNum!, day!, month!);
            } else {
                openCreateTaskModalWithDate(year!, monthNum!, day!);
            }
        });
    });
}

// 日付のタスク一覧を表示するモーダル
function showDayTasksModal(year: string, month: string, day: string, monthLabel: string): void {
    const paddedMonth = String(month).padStart(2, '0');
    const paddedDay = String(day).padStart(2, '0');
    const modalTitle = `${year}/${paddedMonth}/${paddedDay}`;
    const modalLabel = document.getElementById('dayTasksModalLabel');
    if (modalLabel) modalLabel.textContent = modalTitle;

    const modal = document.getElementById('dayTasksModal');
    if (modal) {
        modal.dataset.year = year;
        modal.dataset.month = paddedMonth;
        modal.dataset.day = paddedDay;
    }

    // 「この日にタスクを追加」ボタンのイベント設定
    const addTaskBtn = document.getElementById('addTaskForDayBtn');
    if (addTaskBtn) {
        const newBtn = addTaskBtn.cloneNode(true) as HTMLElement;
        addTaskBtn.parentNode?.replaceChild(newBtn, addTaskBtn);
        newBtn.addEventListener('click', () => {
            $('#dayTasksModal').modal('hide');
            setTimeout(() => openCreateTaskModalWithDate(year, month, day), 300);
        });
    }

    // 「ガントチャートで表示」ボタンのイベント設定
    const ganttViewBtn = document.getElementById('viewGanttForDayBtn');
    if (ganttViewBtn) {
        const newGanttBtn = ganttViewBtn.cloneNode(true) as HTMLElement;
        ganttViewBtn.parentNode?.replaceChild(newGanttBtn, ganttViewBtn);
        newGanttBtn.addEventListener('click', () => {
            window.location.href = `?view_mode=day&target_date=${year}-${paddedMonth}-${paddedDay}`;
        });
    }

    // その日のタスクをfetchで取得
    fetch(`/carbohydratepro/tasks/day/${year}-${month}-${day}/`)
        .then(response => response.json())
        .then((data: TaskApiResponse) => {
            const modalBody = document.getElementById('dayTasksModalBody');
            if (!modalBody) return;

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

                modalBody.querySelectorAll<HTMLElement>('.task-card-mini').forEach(card => {
                    let lastTapTime = 0;
                    let suppressClick = false;
                    let clickCount = 0;
                    let clickTimer: ReturnType<typeof setTimeout> | null = null;
                    const taskId = parseInt(card.dataset['itemId'] ?? '0', 10);

                    card.addEventListener('touchend', (e: TouchEvent) => {
                        const el = e.target as HTMLElement;
                        if (isInteractiveTarget(el) || !!el.closest('.lp-delete-overlay') || card.classList.contains('delete-pending')) return;
                        const now = Date.now();
                        if (now - lastTapTime < 400) {
                            e.preventDefault();
                            suppressClick = true;
                            lastTapTime = 0;
                            if (taskId) openEditTaskModalFromList(taskId);
                        } else {
                            lastTapTime = now;
                        }
                    }, { passive: false });

                    card.addEventListener('click', (e: MouseEvent) => {
                        if (suppressClick) { suppressClick = false; return; }
                        const el = e.target as HTMLElement;
                        if (isInteractiveTarget(el) || !!el.closest('.lp-delete-overlay') || card.classList.contains('delete-pending')) return;
                        clickCount++;
                        if (clickCount === 1) {
                            clickTimer = setTimeout(() => { clickCount = 0; }, 400);
                        } else if (clickCount >= 2) {
                            if (clickTimer !== null) clearTimeout(clickTimer);
                            clickCount = 0;
                            if (taskId) openEditTaskModalFromList(taskId);
                        }
                    });
                });
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
function openEditTaskModalFromList(taskId: number): void {
    $('#dayTasksModal').modal('hide');
    setTimeout(() => openEditTaskModal(taskId), 300);
}

// 一覧モーダルからタスクを削除
function deleteTaskFromList(taskId: number): void {
    if (!confirm('このタスクを削除してもよろしいですか？')) return;

    const csrfToken = document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value || '';

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
function serializeTaskForm(form: HTMLFormElement): string {
    return new URLSearchParams(new FormData(form) as unknown as Record<string, string>).toString();
}

// フォームのエラーメッセージを表示する
function displayTaskFormErrors(form: HTMLFormElement, errors: Record<string, string[]>): void {
    // 既存の動的エラーメッセージをクリア
    form.querySelectorAll('.dynamic-form-error').forEach(el => el.remove());

    const nonFieldErrors: string[] = [];

    for (const [field, messages] of Object.entries(errors)) {
        if (field === '__all__') {
            nonFieldErrors.push(...messages);
        } else {
            // フィールド固有のエラーをフィールドの隣に表示
            const fieldEl = form.querySelector<HTMLElement>(`[name="${field}"], #id_${field}`);
            if (fieldEl?.parentNode) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-danger small dynamic-form-error mt-1';
                errorDiv.textContent = messages.join(' / ');
                fieldEl.parentNode.appendChild(errorDiv);
            } else {
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
async function submitTaskModalForm(form: HTMLFormElement, modalSelector: string): Promise<void> {
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: serializeTaskForm(form),
        });
        const data: TaskModalResponse = await response.json();
        if (data.success) {
            $(modalSelector).modal('hide');
            location.reload();
        } else {
            displayTaskFormErrors(form, data.errors ?? {});
        }
    } catch {
        alert('保存に失敗しました。');
    }
}

// 指定日付で新規タスク作成モーダルを開く
async function openCreateTaskModalWithDate(year: string, month: string, day: string): Promise<void> {
    const selectedDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    try {
        const response = await fetch('/carbohydratepro/tasks/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#createTaskModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;

        const startDateField = document.getElementById('id_start_date') as HTMLInputElement | null;
        const endDateField = document.getElementById('id_end_date') as HTMLInputElement | null;
        if (startDateField) startDateField.value = selectedDate;
        if (endDateField) endDateField.value = selectedDate;

        $('#createTaskModal').modal('show');
        initializeTaskFormControls();

        const form = document.getElementById('createTaskForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitTaskModalForm(form, '#createTaskModal');
            });
        }
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 編集モーダル関連
async function openEditTaskModal(taskId: number): Promise<void> {
    try {
        const response = await fetch(`/carbohydratepro/tasks/edit/${taskId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#editTaskModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
        $('#editTaskModal').modal('show');
        initializeTaskFormControls();

        const form = document.getElementById('editTaskForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitTaskModalForm(form, '#editTaskModal');
            });
        }
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 新規作成モーダル関連
async function openCreateTaskModal(): Promise<void> {
    try {
        const response = await fetch('/carbohydratepro/tasks/create/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#createTaskModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
        $('#createTaskModal').modal('show');
        initializeTaskFormControls();

        const form = document.getElementById('createTaskForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitTaskModalForm(form, '#createTaskModal');
            });
        }
    } catch {
        alert('データの読み込みに失敗しました。');
    }
}

// 月選択フォームのイベント処理
function initializeMonthFilter(): void {
    const monthInput = document.getElementById('target_date');
    monthInput?.addEventListener('change', () => {
        (document.getElementById('monthFilterForm') as HTMLFormElement | null)?.submit();
    });
}

// フィルター関連のイベント処理
function initializeTaskFilters(): void {
    const filterForm = document.getElementById('filterForm') as HTMLFormElement | null;
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            filterForm.submit();
        });
    }

    const statusFilter = document.getElementById('status_filter');
    statusFilter?.addEventListener('change', () => {
        (document.getElementById('filterForm') as HTMLFormElement | null)?.submit();
    });

    const priorityFilter = document.getElementById('priority_filter');
    priorityFilter?.addEventListener('change', () => {
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
    initializeMonthFilter();
    initializeTaskFilters();
    setupCalendarClickEvents();
    initializeTaskFormControls();
    initializeGanttScroll();
});

// ガントチャートの初期スクロール位置を設定
function initializeGanttScroll(): void {
    const ganttContainer = document.getElementById('ganttContainer');
    if (!ganttContainer) return;

    const now = new Date();
    const scrollPosition = (now.getHours() * 100) + (now.getMinutes() * 100 / 60);
    const containerWidth = ganttContainer.clientWidth;
    ganttContainer.scrollLeft = Math.max(0, scrollPosition - (containerWidth / 2));
}

// 時刻を5分刻みで丸める
function roundToNearest5Minutes(date: Date): Date {
    const ms = 5 * 60 * 1000;
    return new Date(Math.round(date.getTime() / ms) * ms);
}

// 時刻をHH:MM形式にフォーマット
function formatTimeHHMM(date: Date): string {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

// 時刻フィールドを時・分の2つのセレクトボックスに置き換える
function initializeTimeSelects(): void {
    ['id_start_time', 'id_end_time'].forEach(inputId => {
        const inputEl = document.getElementById(inputId);
        if (!inputEl || inputEl.dataset.timePickerInitialized) return;
        const input = inputEl as HTMLInputElement;

        const currentValue = input.value;
        const parts = currentValue ? currentValue.split(':') : [];
        const currentHour = parts[0] ?? '';
        const currentMinute = parts[1] ?? '';

        // フォーム送信用の隠しフィールド（idとnameを保持）
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = input.id;
        hiddenInput.name = input.name;
        hiddenInput.value = currentValue;
        hiddenInput.dataset.timePickerInitialized = 'true';

        // 時セレクト
        const hourSelect = document.createElement('select');
        hourSelect.className = 'form-control form-control-sm time-hour-select';
        hourSelect.style.width = 'auto';
        const emptyHour = document.createElement('option');
        emptyHour.value = '';
        emptyHour.textContent = '--';
        hourSelect.appendChild(emptyHour);
        for (let h = 0; h < 24; h++) {
            const opt = document.createElement('option');
            opt.value = String(h).padStart(2, '0');
            opt.textContent = String(h).padStart(2, '0');
            if (currentHour !== '' && parseInt(currentHour) === h) opt.selected = true;
            hourSelect.appendChild(opt);
        }

        // 分セレクト（5分刻み）
        const minuteSelect = document.createElement('select');
        minuteSelect.className = 'form-control form-control-sm time-minute-select';
        minuteSelect.style.width = 'auto';
        const emptyMinute = document.createElement('option');
        emptyMinute.value = '';
        emptyMinute.textContent = '--';
        minuteSelect.appendChild(emptyMinute);
        for (let m = 0; m < 60; m += 5) {
            const opt = document.createElement('option');
            opt.value = String(m).padStart(2, '0');
            opt.textContent = String(m).padStart(2, '0');
            if (currentMinute !== '' && parseInt(currentMinute) === m) opt.selected = true;
            minuteSelect.appendChild(opt);
        }

        // 隠しフィールドへ同期
        const syncHidden = (): void => {
            hiddenInput.value = (hourSelect.value && minuteSelect.value)
                ? `${hourSelect.value}:${minuteSelect.value}`
                : '';
            const form = hiddenInput.closest('form') as HTMLFormElement | null;
            if (form) validateAndFixDateTimeOrder(form);
        };
        hourSelect.addEventListener('change', syncHidden);
        minuteSelect.addEventListener('change', syncHidden);

        // ラッパー
        const wrapper = document.createElement('div');
        wrapper.className = 'time-picker-wrapper d-inline-flex align-items-center';
        wrapper.style.gap = '4px';
        wrapper.dataset.timePickerFor = inputId;
        const sep = document.createElement('span');
        sep.className = 'mx-1';
        sep.textContent = ':';
        wrapper.appendChild(hourSelect);
        wrapper.appendChild(sep);
        wrapper.appendChild(minuteSelect);
        wrapper.appendChild(hiddenInput);

        input.replaceWith(wrapper);
    });
}

// 時刻ピッカー（隠し入力 + 時・分セレクト）に値をセット
function setTimePickerValue(inputId: string, timeStr: string): void {
    const hiddenInput = document.getElementById(inputId) as HTMLInputElement | null;
    if (!hiddenInput) return;
    hiddenInput.value = timeStr;
    const wrapper = hiddenInput.closest<HTMLElement>('.time-picker-wrapper');
    if (!wrapper) return;
    const [hourStr = '', minuteStr = ''] = timeStr ? timeStr.split(':') : [];
    const hourSelect = wrapper.querySelector<HTMLSelectElement>('.time-hour-select');
    const minuteSelect = wrapper.querySelector<HTMLSelectElement>('.time-minute-select');
    if (hourSelect) hourSelect.value = hourStr;
    if (minuteSelect) {
        const rounded = Math.round(parseInt(minuteStr || '0') / 5) * 5;
        minuteSelect.value = String(rounded % 60).padStart(2, '0');
    }
}

// デフォルト時刻を設定（新規作成時のみ：値が空の場合）
function setDefaultTimes(): void {
    const startHidden = document.getElementById('id_start_time') as HTMLInputElement | null;
    const endHidden = document.getElementById('id_end_time') as HTMLInputElement | null;
    if (!startHidden || !endHidden) return;
    if (startHidden.value || endHidden.value) return;

    const now = new Date();
    const rounded = roundToNearest5Minutes(now);
    const oneHourLater = new Date(rounded.getTime() + 60 * 60 * 1000);

    setTimePickerValue('id_start_time', formatTimeHHMM(rounded));
    setTimePickerValue('id_end_time', formatTimeHHMM(oneHourLater));
}

// 開始日変更時のイベント処理（終了日を同じ幅で移動・終了日ピッカーを自動オープン）
function handleStartDateChange(event: Event): void {
    const startDateInput = event.target as HTMLInputElement;
    const form = startDateInput.closest('form') as HTMLFormElement | null;
    if (!form) return;

    const endDateInput = form.querySelector<HTMLInputElement>('#id_end_date');
    if (!endDateInput) return;

    const previousStartDateStr = startDateInput.dataset.previousValue ?? '';
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
    } else if (!endDateInput.value) {
        endDateInput.value = currentStartDateStr;
    }

    startDateInput.dataset.previousValue = currentStartDateStr;

    // 終了日ピッカーを自動で開く
    try {
        (endDateInput as HTMLInputElement & { showPicker?: () => void }).showPicker?.();
    } catch {
        endDateInput.focus();
    }

    validateAndFixDateTimeOrder(form);
}

// 開始日時 > 終了日時の場合に自動修正する
function validateAndFixDateTimeOrder(form: HTMLFormElement): void {
    const startDateInput = form.querySelector<HTMLInputElement>('#id_start_date');
    const endDateInput = form.querySelector<HTMLInputElement>('#id_end_date');
    const startTimeEl = form.querySelector('#id_start_time') as HTMLInputElement | HTMLSelectElement | null;
    const endTimeEl = form.querySelector('#id_end_time') as HTMLInputElement | HTMLSelectElement | null;
    const allDayCheckbox = form.querySelector<HTMLInputElement>('#id_all_day');

    if (!startDateInput || !endDateInput) return;

    const startDateStr = startDateInput.value;
    const endDateStr = endDateInput.value;
    if (!startDateStr || !endDateStr) return;

    const isAllDay = allDayCheckbox?.checked ?? false;
    const startTimeStr = isAllDay ? '00:00' : (startTimeEl?.value ?? '');
    const endTimeStr = isAllDay ? '23:59' : (endTimeEl?.value ?? '');

    if (!isAllDay && (!startTimeStr || !endTimeStr)) return;

    const startDatetime = new Date(`${startDateStr}T${startTimeStr}:00`);
    const endDatetime = new Date(`${endDateStr}T${endTimeStr}:00`);

    if (isNaN(startDatetime.getTime()) || isNaN(endDatetime.getTime())) return;

    if (startDatetime > endDatetime) {
        // 終了日を開始日に合わせる
        endDateInput.value = startDateStr;

        if (!isAllDay && startTimeEl && endTimeEl) {
            // 終了時刻を開始時刻の1時間後に設定
            const parts = startTimeStr.split(':');
            const startHour = parseInt(parts[0]);
            const startMinute = parseInt(parts[1]);
            const endHour = startHour + 1;

            const newEndTimeStr = endHour >= 24
                ? '23:55'
                : `${String(endHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
            setTimePickerValue('id_end_time', newEndTimeStr);
        }
    }
}

// タスクフォーム制御の初期化
function initializeTaskFormControls(): void {
    // 時刻フィールドをセレクトボックスに変換（他の処理より先に行う）
    initializeTimeSelects();

    const allDayCheckbox = document.querySelector<HTMLInputElement>('#id_all_day');
    if (allDayCheckbox) {
        toggleTimeFields();
        allDayCheckbox.addEventListener('change', toggleTimeFields);
    }

    const frequencySelect = document.querySelector<HTMLSelectElement>('#id_frequency');
    if (frequencySelect) {
        toggleRepeatFields();
        frequencySelect.addEventListener('change', toggleRepeatFields);
    }

    // デフォルト時刻を設定（新規作成時のみ）
    setDefaultTimes();

    // 開始日変更イベントを設定
    const startDateInput = document.querySelector<HTMLInputElement>('#id_start_date');
    if (startDateInput) {
        startDateInput.dataset.previousValue = startDateInput.value;
        startDateInput.addEventListener('change', handleStartDateChange);
    }

    // 日時の整合性チェックイベントを設定
    const form = document.querySelector<HTMLFormElement>('#createTaskForm, #editTaskForm');
    if (form) {
        ['#id_end_date', '#id_start_time', '#id_end_time'].forEach(selector => {
            form.querySelector(selector)?.addEventListener('change', () => {
                validateAndFixDateTimeOrder(form);
            });
        });
    }
}

// 時間フィールドの表示/非表示を切り替え
function toggleTimeFields(): void {
    const allDayCheckbox = document.querySelector<HTMLInputElement>('#id_all_day');
    const timeFields = document.querySelectorAll<HTMLElement>('.time-field');

    if (allDayCheckbox && timeFields.length > 0) {
        const isAllDay = allDayCheckbox.checked;
        timeFields.forEach(field => {
            field.style.display = isAllDay ? 'none' : 'block';
            if (isAllDay) {
                // 時・分セレクトをクリア
                field.querySelectorAll<HTMLSelectElement>('.time-hour-select, .time-minute-select').forEach(sel => {
                    sel.value = '';
                });
                // 隠しフィールドもクリア
                field.querySelectorAll<HTMLInputElement>('input[data-time-picker-initialized]').forEach(inp => {
                    inp.value = '';
                });
            }
        });
    }
}

// 繰り返し設定フィールドの表示/非表示を切り替え
function toggleRepeatFields(): void {
    const frequencySelect = document.querySelector<HTMLSelectElement>('#id_frequency');
    const repeatFields = document.querySelectorAll<HTMLElement>('.repeat-field');

    if (frequencySelect && repeatFields.length > 0) {
        const hasFrequency = frequencySelect.value && frequencySelect.value !== '';
        repeatFields.forEach(field => {
            field.style.display = hasFrequency ? 'block' : 'none';
        });
    }
}
