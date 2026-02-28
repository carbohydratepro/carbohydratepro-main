// 一時タスク管理（カンバンボード）用 JavaScript

const TEMP_TASK_KEY = 'temp_tasks_v1';

let draggedTaskId: string | null = null;
let dragSourceEl: HTMLElement | null = null;

// タッチドラッグ用の状態管理
interface TouchState {
  taskId: string | null;
  startX: number;
  startY: number;
  cloneEl: HTMLElement | null;
  sourceEl: HTMLElement | null;
}

const touch: TouchState = {
    taskId: null,
    startX: 0,
    startY: 0,
    cloneEl: null,
    sourceEl: null,
};

// =========================================================
// データ管理
// =========================================================

interface TempTask {
  id: string;
  title: string;
  status: string;
  createdAt: string;
}

function loadTasks(): TempTask[] {
    try {
        return JSON.parse(localStorage.getItem(TEMP_TASK_KEY) || '[]') as TempTask[];
    } catch {
        return [];
    }
}

function saveTasks(tasks: TempTask[]): void {
    localStorage.setItem(TEMP_TASK_KEY, JSON.stringify(tasks));
}

function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

// =========================================================
// タスク操作
// =========================================================

function addTask(status: string): void {
    const input = document.getElementById(`input-${status}`) as HTMLInputElement | null;
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

function deleteTask(id: string): void {
    saveTasks(loadTasks().filter(t => t.id !== id));
    renderAll();
}

function moveTask(id: string, newStatus: string): void {
    const tasks = loadTasks();
    const task = tasks.find(t => t.id === id);
    if (task && task.status !== newStatus) {
        task.status = newStatus;
        saveTasks(tasks);
        renderAll();
    }
}

function clearAllTasks(): void {
    if (!confirm('すべてのタスクを削除してもよろしいですか？')) return;
    saveTasks([]);
    renderAll();
}

// =========================================================
// レンダリング
// =========================================================

function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function renderColumn(status: string): void {
    const container = document.getElementById(`tasks-${status}`);
    const countEl = document.getElementById(`count-${status}`);
    if (!container) return;

    const tasks = loadTasks().filter(t => t.status === status);
    container.innerHTML = '';
    tasks.forEach(task => container.appendChild(createTaskCard(task)));

    if (countEl) countEl.textContent = String(tasks.length);
}

function renderAll(): void {
    renderColumn('todo');
    renderColumn('doing');
    renderColumn('done');
}

function createTaskCard(task: TempTask): HTMLElement {
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
    card.querySelector('.kanban-task-delete')?.addEventListener('click', (e) => {
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

function handleDragStart(e: DragEvent): void {
    dragSourceEl = e.currentTarget as HTMLElement;
    draggedTaskId = dragSourceEl.dataset.taskId || null;
    dragSourceEl.classList.add('dragging');
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedTaskId || '');
    }
}

function handleDragEnd(_e: DragEvent): void {
    if (dragSourceEl) dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedTaskId = null;
    clearAllDragOver();
}

function handleDropZoneDragOver(e: DragEvent): void {
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
    const target = e.currentTarget as HTMLElement;
    target.classList.add('drag-over');
}

function handleDropZoneDragLeave(e: DragEvent): void {
    const target = e.currentTarget as HTMLElement;
    // 子要素へのmoveは無視する
    if (target.contains(e.relatedTarget as Node)) return;
    target.classList.remove('drag-over');
}

function handleDrop(e: DragEvent, status: string): void {
    e.preventDefault();
    const target = e.currentTarget as HTMLElement;
    target.classList.remove('drag-over');
    if (draggedTaskId) moveTask(draggedTaskId, status);
}

function handleTrashDrop(e: DragEvent): void {
    e.preventDefault();
    const target = e.currentTarget as HTMLElement;
    target.classList.remove('drag-over');
    if (draggedTaskId) deleteTask(draggedTaskId);
}

function clearAllDragOver(): void {
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
}

// =========================================================
// モバイル タッチドラッグ
// =========================================================

function handleTouchStart(e: TouchEvent): void {
    // 削除ボタンのタッチは無視
    if ((e.target as HTMLElement).closest('.kanban-task-delete')) return;

    const t = e.touches[0];
    const card = e.currentTarget as HTMLElement;
    touch.taskId = card.dataset.taskId || null;
    touch.startX = t.clientX;
    touch.startY = t.clientY;
    touch.sourceEl = card;

    // 少し待ってからドラッグ開始（タップと区別するため）
    const rect = card.getBoundingClientRect();

    const clone = card.cloneNode(true) as HTMLElement;
    clone.className = card.className + ' touch-clone';
    clone.style.width = rect.width + 'px';
    clone.style.top = rect.top + 'px';
    clone.style.left = rect.left + 'px';
    document.body.appendChild(clone);
    touch.cloneEl = clone;

    card.style.opacity = '0.3';
    e.preventDefault();
}

function handleTouchMove(e: TouchEvent): void {
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
        (elBelow as HTMLElement).closest('.kanban-tasks') ||
        (elBelow as HTMLElement).closest('.kanban-trash')
    );
    if (dropTarget) dropTarget.classList.add('drag-over');
}

function handleTouchEnd(e: TouchEvent): void {
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

    const tasksEl = elBelow.closest('.kanban-tasks') as HTMLElement | null;
    const trashEl = elBelow.closest('.kanban-trash');

    if (tasksEl) {
        const column = tasksEl.closest('.kanban-column') as HTMLElement | null;
        if (column) moveTask(touch.taskId, column.dataset.status || '');
    } else if (trashEl) {
        deleteTask(touch.taskId);
    }

    touch.taskId = null;
}

// =========================================================
// 入力イベント
// =========================================================

function handleInputKeypress(e: KeyboardEvent): void {
    if (e.key === 'Enter') {
        e.preventDefault();
        const input = e.currentTarget as HTMLInputElement;
        addTask(input.dataset.status || '');
    }
}

// =========================================================
// ドロップゾーン初期化
// =========================================================

function initializeDropZones(): void {
    document.querySelectorAll<HTMLElement>('.kanban-tasks').forEach(container => {
        const column = container.closest('.kanban-column') as HTMLElement | null;
        const status = column ? column.dataset.status || '' : '';

        container.addEventListener('dragover', handleDropZoneDragOver);
        container.addEventListener('dragleave', handleDropZoneDragLeave);
        container.addEventListener('drop', (e) => handleDrop(e as DragEvent, status));
    });

    const trash = document.getElementById('trashArea');
    if (trash) {
        trash.addEventListener('dragover', handleDropZoneDragOver);
        trash.addEventListener('dragleave', (e) => {
            const target = e.currentTarget as HTMLElement;
            if (target.contains(e.relatedTarget as Node)) return;
            target.classList.remove('drag-over');
        });
        trash.addEventListener('drop', (e) => handleTrashDrop(e as DragEvent));
    }
}

function initializeInputs(): void {
    document.querySelectorAll<HTMLElement>('.kanban-input').forEach(el => {
        el.addEventListener('keypress', (e) => handleInputKeypress(e as KeyboardEvent));
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
