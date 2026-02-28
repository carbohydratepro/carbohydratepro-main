"use strict";
// 一時タスク管理（カンバンボード）用 JavaScript
const TEMP_TASK_KEY = 'temp_tasks_v1';
const DRAG_THRESHOLD = 10; // ドラッグ開始とみなす移動距離(px)
const DOUBLE_TAP_DELAY = 300; // ダブルタップ検出の時間枠(ms)
let draggedTaskId = null;
let dragSourceEl = null;
const touch = {
    taskId: null,
    startX: 0,
    startY: 0,
    cloneEl: null,
    sourceEl: null,
    isDragging: false,
};
// ダブルタップ検出用
const doubleTapState = { time: 0, taskId: '' };
function loadTasks() {
    try {
        return JSON.parse(localStorage.getItem(TEMP_TASK_KEY) || '[]');
    }
    catch (_a) {
        return [];
    }
}
function saveTasks(tasks) {
    localStorage.setItem(TEMP_TASK_KEY, JSON.stringify(tasks));
}
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
}
// =========================================================
// タスク操作
// =========================================================
function addTask(status) {
    const input = document.getElementById(`input-${status}`);
    if (!input)
        return;
    const title = input.value.trim();
    if (!title) {
        input.focus();
        return;
    }
    const tasks = loadTasks();
    tasks.push({ id: generateId(), title, status, createdAt: new Date().toISOString() });
    saveTasks(tasks);
    input.value = '';
    renderAll();
    input.focus();
}
function deleteTask(id) {
    saveTasks(loadTasks().filter(t => t.id !== id));
    renderAll();
}
function moveTask(id, newStatus) {
    const tasks = loadTasks();
    const task = tasks.find(t => t.id === id);
    if (task && task.status !== newStatus) {
        task.status = newStatus;
        saveTasks(tasks);
        renderAll();
    }
}
function clearAllTasks() {
    if (!confirm('すべてのタスクを削除してもよろしいですか？'))
        return;
    saveTasks([]);
    renderAll();
}
// =========================================================
// インライン編集
// =========================================================
function startEditTask(id, cardEl) {
    const textEl = cardEl.querySelector('.kanban-task-text');
    if (!textEl)
        return;
    const tasks = loadTasks();
    const task = tasks.find(t => t.id === id);
    if (!task)
        return;
    // ドラッグ無効化・編集スタイル
    cardEl.draggable = false;
    cardEl.classList.add('editing');
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'kanban-task-edit-input';
    input.value = task.title;
    textEl.replaceWith(input);
    input.focus();
    input.select();
    let committed = false;
    const commit = () => {
        if (committed)
            return;
        committed = true;
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== task.title) {
            task.title = newTitle;
            saveTasks(tasks);
        }
        renderAll();
    };
    const cancel = () => {
        if (committed)
            return;
        committed = true;
        input.removeEventListener('blur', commit);
        renderAll();
    };
    input.addEventListener('blur', commit);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            commit();
        }
        else if (e.key === 'Escape') {
            e.preventDefault();
            cancel();
        }
    });
}
// =========================================================
// ドラッグオーバーレイ
// =========================================================
function showDragOverlay() {
    const overlay = document.getElementById('dragOverlay');
    if (overlay)
        overlay.classList.add('active');
}
function hideDragOverlay() {
    const overlay = document.getElementById('dragOverlay');
    if (overlay)
        overlay.classList.remove('active');
    document.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-over'));
}
function initializeOverlay() {
    const overlay = document.getElementById('dragOverlay');
    if (!overlay)
        return;
    // オーバーレイ背景（ゾーン外）ではドロップ不可
    overlay.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (e.dataTransfer)
            e.dataTransfer.dropEffect = 'none';
    });
    document.querySelectorAll('.drag-zone').forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (e.dataTransfer)
                e.dataTransfer.dropEffect = 'move';
            document.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-over'));
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', (e) => {
            if (!zone.contains(e.relatedTarget)) {
                zone.classList.remove('drag-over');
            }
        });
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            zone.classList.remove('drag-over');
            if (!draggedTaskId)
                return;
            const action = zone.dataset.action;
            if (action === 'delete') {
                deleteTask(draggedTaskId);
            }
            else if (action && action !== 'cancel') {
                moveTask(draggedTaskId, action);
            }
            hideDragOverlay();
        });
    });
}
// =========================================================
// レンダリング
// =========================================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}
function renderColumn(status) {
    const container = document.getElementById(`tasks-${status}`);
    const countEl = document.getElementById(`count-${status}`);
    if (!container)
        return;
    const tasks = loadTasks().filter(t => t.status === status);
    container.innerHTML = '';
    tasks.forEach(task => container.appendChild(createTaskCard(task)));
    if (countEl)
        countEl.textContent = String(tasks.length);
}
function renderAll() {
    renderColumn('todo');
    renderColumn('doing');
    renderColumn('done');
}
function createTaskCard(task) {
    var _a;
    const card = document.createElement('div');
    card.className = 'kanban-task-card';
    card.dataset.taskId = task.id;
    card.draggable = true;
    card.title = 'ダブルクリックで編集 / ドラッグで移動';
    card.innerHTML = `
        <span class="kanban-task-text">${escapeHtml(task.title)}</span>
        <button class="kanban-task-delete" title="削除" data-id="${task.id}">
            <i class="fas fa-times"></i>
        </button>
    `;
    // 削除ボタン
    (_a = card.querySelector('.kanban-task-delete')) === null || _a === void 0 ? void 0 : _a.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteTask(task.id);
    });
    // PC: ダブルクリックで編集
    card.addEventListener('dblclick', (e) => {
        if (e.target.closest('.kanban-task-delete'))
            return;
        startEditTask(task.id, card);
    });
    // PC: HTML5 Drag & Drop
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    // モバイル: タッチイベント
    card.addEventListener('touchstart', handleTouchStart, { passive: false });
    card.addEventListener('touchmove', handleTouchMove, { passive: false });
    card.addEventListener('touchend', handleTouchEnd, { passive: false });
    return card;
}
// =========================================================
// PC ドラッグ & ドロップ
// =========================================================
function handleDragStart(e) {
    dragSourceEl = e.currentTarget;
    draggedTaskId = dragSourceEl.dataset.taskId || null;
    dragSourceEl.classList.add('dragging');
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedTaskId || '');
    }
    // ブラウザのD&Dゴースト生成後にオーバーレイ表示
    requestAnimationFrame(() => showDragOverlay());
}
function handleDragEnd(_e) {
    if (dragSourceEl)
        dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedTaskId = null;
    hideDragOverlay();
}
// フォールバック: カラムへの直接ドロップ
function handleDropZoneDragOver(e) {
    e.preventDefault();
    if (e.dataTransfer)
        e.dataTransfer.dropEffect = 'move';
    const target = e.currentTarget;
    target.classList.add('drag-over');
}
function handleDropZoneDragLeave(e) {
    const target = e.currentTarget;
    if (target.contains(e.relatedTarget))
        return;
    target.classList.remove('drag-over');
}
function handleDrop(e, status) {
    e.preventDefault();
    const target = e.currentTarget;
    target.classList.remove('drag-over');
    if (draggedTaskId)
        moveTask(draggedTaskId, status);
    hideDragOverlay();
}
function clearAllDragOver() {
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
}
// =========================================================
// モバイル タッチドラッグ
// =========================================================
function handleTouchStart(e) {
    if (e.target.closest('.kanban-task-delete'))
        return;
    if (e.target.closest('.kanban-task-edit-input'))
        return;
    const card = e.currentTarget;
    const taskId = card.dataset.taskId || '';
    const t = e.touches[0];
    touch.taskId = taskId;
    touch.startX = t.clientX;
    touch.startY = t.clientY;
    touch.sourceEl = card;
    touch.cloneEl = null;
    touch.isDragging = false;
    e.preventDefault();
}
function handleTouchMove(e) {
    if (!touch.taskId || !touch.sourceEl)
        return;
    e.preventDefault();
    const t = e.touches[0];
    const dx = t.clientX - touch.startX;
    const dy = t.clientY - touch.startY;
    // 閾値を超えたらドラッグ開始
    if (!touch.isDragging) {
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < DRAG_THRESHOLD)
            return;
        touch.isDragging = true;
        // ダブルタップ状態をリセット（ドラッグ開始時は編集しない）
        doubleTapState.time = 0;
        doubleTapState.taskId = '';
        const card = touch.sourceEl;
        const rect = card.getBoundingClientRect();
        const clone = card.cloneNode(true);
        clone.className = card.className + ' touch-clone';
        clone.style.width = rect.width + 'px';
        clone.style.top = (rect.top + dy) + 'px';
        clone.style.left = (rect.left + dx) + 'px';
        document.body.appendChild(clone);
        touch.cloneEl = clone;
        card.style.opacity = '0.3';
        showDragOverlay();
    }
    if (!touch.cloneEl)
        return;
    // クローンを指の位置へ移動
    const rect = touch.sourceEl.getBoundingClientRect();
    touch.cloneEl.style.left = (rect.left + dx) + 'px';
    touch.cloneEl.style.top = (rect.top + dy) + 'px';
    // オーバーレイゾーンのハイライト
    document.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-over'));
    touch.cloneEl.style.display = 'none';
    const elBelow = document.elementFromPoint(t.clientX, t.clientY);
    touch.cloneEl.style.display = '';
    const zone = elBelow === null || elBelow === void 0 ? void 0 : elBelow.closest('.drag-zone');
    if (zone)
        zone.classList.add('drag-over');
}
function handleTouchEnd(e) {
    if (!touch.taskId)
        return;
    if (!touch.isDragging) {
        // タップ → ダブルタップ検出
        const now = Date.now();
        const taskId = touch.taskId;
        const sourceEl = touch.sourceEl;
        if (taskId === doubleTapState.taskId && now - doubleTapState.time < DOUBLE_TAP_DELAY) {
            // ダブルタップ確定 → 編集開始
            doubleTapState.time = 0;
            doubleTapState.taskId = '';
            if (sourceEl)
                startEditTask(taskId, sourceEl);
            e.preventDefault();
        }
        else {
            // 1回目のタップ
            doubleTapState.time = now;
            doubleTapState.taskId = taskId;
        }
        touch.taskId = null;
        touch.sourceEl = null;
        touch.isDragging = false;
        return;
    }
    // ドラッグ終了処理
    const t = e.changedTouches[0];
    if (touch.cloneEl) {
        document.body.removeChild(touch.cloneEl);
        touch.cloneEl = null;
    }
    if (touch.sourceEl) {
        touch.sourceEl.style.opacity = '';
        touch.sourceEl = null;
    }
    hideDragOverlay();
    clearAllDragOver();
    // ドロップ先ゾーンを判定
    const elBelow = document.elementFromPoint(t.clientX, t.clientY);
    if (elBelow && touch.taskId) {
        const zone = elBelow.closest('.drag-zone');
        if (zone) {
            const action = zone.dataset.action;
            if (action === 'delete') {
                deleteTask(touch.taskId);
            }
            else if (action && action !== 'cancel') {
                moveTask(touch.taskId, action);
            }
        }
    }
    touch.taskId = null;
    touch.isDragging = false;
}
// =========================================================
// 入力イベント
// =========================================================
function handleInputKeypress(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const input = e.currentTarget;
        addTask(input.dataset.status || '');
    }
}
// =========================================================
// 初期化
// =========================================================
function initializeDropZones() {
    // フォールバック用カラムドロップゾーン
    document.querySelectorAll('.kanban-tasks').forEach(container => {
        const column = container.closest('.kanban-column');
        const status = column ? column.dataset.status || '' : '';
        container.addEventListener('dragover', handleDropZoneDragOver);
        container.addEventListener('dragleave', handleDropZoneDragLeave);
        container.addEventListener('drop', (e) => handleDrop(e, status));
    });
}
function initializeInputs() {
    document.querySelectorAll('.kanban-input').forEach(el => {
        el.addEventListener('keypress', (e) => handleInputKeypress(e));
    });
}
document.addEventListener('DOMContentLoaded', () => {
    initializeOverlay();
    initializeDropZones();
    initializeInputs();
    renderAll();
});
