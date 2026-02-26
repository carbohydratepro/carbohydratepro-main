// 一時タスク管理（カンバンボード）用 JavaScript

const TEMP_TASK_KEY = 'temp_tasks_v1';

/** @type {string|null} */
let draggedTaskId = null;

/** @type {HTMLElement|null} */
let dragSourceEl = null;

// タッチドラッグ用の状態管理
/** @type {{ taskId: string|null, startX: number, startY: number, cloneEl: HTMLElement|null, sourceEl: HTMLElement|null }} */
const touch = {
    taskId: null,
    startX: 0,
    startY: 0,
    cloneEl: null,
    sourceEl: null,
};

// =========================================================
// データ管理
// =========================================================

/**
 * @typedef {{ id: string, title: string, status: string, createdAt: string }} TempTask
 */

/**
 * @returns {TempTask[]}
 */
function loadTasks() {
    try {
        return JSON.parse(localStorage.getItem(TEMP_TASK_KEY) || '[]');
    } catch {
        return [];
    }
}

/**
 * @param {TempTask[]} tasks
 */
function saveTasks(tasks) {
    localStorage.setItem(TEMP_TASK_KEY, JSON.stringify(tasks));
}

/** @returns {string} */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

// =========================================================
// タスク操作
// =========================================================

/** @param {string} status */
function addTask(status) {
    const input = document.getElementById(`input-${status}`);
    if (!input) return;
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

/** @param {string} id */
function deleteTask(id) {
    saveTasks(loadTasks().filter(t => t.id !== id));
    renderAll();
}

/**
 * @param {string} id
 * @param {string} newStatus
 */
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
    if (!confirm('すべてのタスクを削除してもよろしいですか？')) return;
    saveTasks([]);
    renderAll();
}

// =========================================================
// レンダリング
// =========================================================

/**
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

/** @param {string} status */
function renderColumn(status) {
    const container = document.getElementById(`tasks-${status}`);
    const countEl = document.getElementById(`count-${status}`);
    if (!container) return;

    const tasks = loadTasks().filter(t => t.status === status);
    container.innerHTML = '';
    tasks.forEach(task => container.appendChild(createTaskCard(task)));

    if (countEl) countEl.textContent = String(tasks.length);
}

function renderAll() {
    renderColumn('todo');
    renderColumn('doing');
    renderColumn('done');
}

/**
 * @param {TempTask} task
 * @returns {HTMLElement}
 */
function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'kanban-task-card';
    card.dataset.taskId = task.id;
    card.draggable = true;
    card.innerHTML = `
        <span class="kanban-task-text">${escapeHtml(task.title)}</span>
        <button class="kanban-task-delete" title="削除" data-id="${task.id}">
            <i class="fas fa-times"></i>
        </button>
    `;

    // 削除ボタン
    card.querySelector('.kanban-task-delete').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteTask(task.id);
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

/** @param {DragEvent} e */
function handleDragStart(e) {
    dragSourceEl = /** @type {HTMLElement} */ (e.currentTarget);
    draggedTaskId = dragSourceEl.dataset.taskId || null;
    dragSourceEl.classList.add('dragging');
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedTaskId || '');
    }
}

/** @param {DragEvent} e */
function handleDragEnd(e) {
    if (dragSourceEl) dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedTaskId = null;
    clearAllDragOver();
}

/** @param {DragEvent} e */
function handleDropZoneDragOver(e) {
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
    const target = /** @type {HTMLElement} */ (e.currentTarget);
    target.classList.add('drag-over');
}

/** @param {DragEvent} e */
function handleDropZoneDragLeave(e) {
    const target = /** @type {HTMLElement} */ (e.currentTarget);
    // 子要素へのmoveは無視する
    if (target.contains(/** @type {Node} */ (e.relatedTarget))) return;
    target.classList.remove('drag-over');
}

/**
 * @param {DragEvent} e
 * @param {string} status
 */
function handleDrop(e, status) {
    e.preventDefault();
    const target = /** @type {HTMLElement} */ (e.currentTarget);
    target.classList.remove('drag-over');
    if (draggedTaskId) moveTask(draggedTaskId, status);
}

/** @param {DragEvent} e */
function handleTrashDrop(e) {
    e.preventDefault();
    const target = /** @type {HTMLElement} */ (e.currentTarget);
    target.classList.remove('drag-over');
    if (draggedTaskId) deleteTask(draggedTaskId);
}

function clearAllDragOver() {
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
}

// =========================================================
// モバイル タッチドラッグ
// =========================================================

/** @param {TouchEvent} e */
function handleTouchStart(e) {
    // 削除ボタンのタッチは無視
    if (/** @type {HTMLElement} */ (e.target).closest('.kanban-task-delete')) return;

    const t = e.touches[0];
    const card = /** @type {HTMLElement} */ (e.currentTarget);
    touch.taskId = card.dataset.taskId || null;
    touch.startX = t.clientX;
    touch.startY = t.clientY;
    touch.sourceEl = card;

    // 少し待ってからドラッグ開始（タップと区別するため）
    const rect = card.getBoundingClientRect();

    const clone = /** @type {HTMLElement} */ (card.cloneNode(true));
    clone.className = card.className + ' touch-clone';
    clone.style.width = rect.width + 'px';
    clone.style.top = rect.top + 'px';
    clone.style.left = rect.left + 'px';
    document.body.appendChild(clone);
    touch.cloneEl = clone;

    card.style.opacity = '0.3';
    e.preventDefault();
}

/** @param {TouchEvent} e */
function handleTouchMove(e) {
    if (!touch.cloneEl || !touch.taskId) return;
    e.preventDefault();

    const t = e.touches[0];
    const dx = t.clientX - touch.startX;
    const dy = t.clientY - touch.startY;

    if (touch.cloneEl && touch.sourceEl) {
        const rect = touch.sourceEl.getBoundingClientRect();
        touch.cloneEl.style.left = (rect.left + dx) + 'px';
        touch.cloneEl.style.top = (rect.top + dy) + 'px';
    }

    // ドロップターゲットのハイライト
    clearAllDragOver();
    touch.cloneEl.style.display = 'none';
    const elBelow = document.elementFromPoint(t.clientX, t.clientY);
    touch.cloneEl.style.display = '';

    const dropTarget = elBelow && (
        /** @type {HTMLElement} */ (elBelow).closest('.kanban-tasks') ||
        /** @type {HTMLElement} */ (elBelow).closest('.kanban-trash')
    );
    if (dropTarget) dropTarget.classList.add('drag-over');
}

/** @param {TouchEvent} e */
function handleTouchEnd(e) {
    if (!touch.cloneEl || !touch.taskId) return;

    const t = e.changedTouches[0];

    // クローン削除・透明度リセット
    document.body.removeChild(touch.cloneEl);
    touch.cloneEl = null;
    if (touch.sourceEl) {
        touch.sourceEl.style.opacity = '';
        touch.sourceEl = null;
    }
    clearAllDragOver();

    // ドロップ先を判定
    const elBelow = document.elementFromPoint(t.clientX, t.clientY);
    if (!elBelow) { touch.taskId = null; return; }

    const tasksEl = /** @type {HTMLElement|null} */ (elBelow.closest('.kanban-tasks'));
    const trashEl = elBelow.closest('.kanban-trash');

    if (tasksEl) {
        const column = /** @type {HTMLElement|null} */ (tasksEl.closest('.kanban-column'));
        if (column) moveTask(touch.taskId, column.dataset.status || '');
    } else if (trashEl) {
        deleteTask(touch.taskId);
    }

    touch.taskId = null;
}

// =========================================================
// 入力イベント
// =========================================================

/** @param {KeyboardEvent} e */
function handleInputKeypress(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const input = /** @type {HTMLInputElement} */ (e.currentTarget);
        addTask(input.dataset.status || '');
    }
}

// =========================================================
// ドロップゾーン初期化
// =========================================================

function initializeDropZones() {
    document.querySelectorAll('.kanban-tasks').forEach(el => {
        const container = /** @type {HTMLElement} */ (el);
        const column = /** @type {HTMLElement|null} */ (container.closest('.kanban-column'));
        const status = column ? column.dataset.status || '' : '';

        container.addEventListener('dragover', handleDropZoneDragOver);
        container.addEventListener('dragleave', handleDropZoneDragLeave);
        container.addEventListener('drop', (e) => handleDrop(/** @type {DragEvent} */ (e), status));
    });

    const trash = document.getElementById('trashArea');
    if (trash) {
        trash.addEventListener('dragover', handleDropZoneDragOver);
        trash.addEventListener('dragleave', (e) => {
            const target = /** @type {HTMLElement} */ (e.currentTarget);
            if (target.contains(/** @type {Node} */ (e.relatedTarget))) return;
            target.classList.remove('drag-over');
        });
        trash.addEventListener('drop', handleTrashDrop);
    }
}

function initializeInputs() {
    document.querySelectorAll('.kanban-input').forEach(el => {
        el.addEventListener('keypress', handleInputKeypress);
    });
}

// =========================================================
// 初期化
// =========================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeDropZones();
    initializeInputs();
    renderAll();
});
