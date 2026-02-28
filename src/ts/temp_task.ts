// 一時タスク管理（カンバンボード）用 TypeScript

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
  isDragging: boolean;
}

const touch: TouchState = {
    taskId: null,
    startX: 0,
    startY: 0,
    cloneEl: null,
    sourceEl: null,
    isDragging: false,
};

// ダブルタップ検出用
let lastTapTime = 0;
let lastTapTaskId: string | null = null;

const DRAG_THRESHOLD = 8; // px

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

function updateTask(id: string, newTitle: string): void {
    const tasks = loadTasks();
    const task = tasks.find(t => t.id === id);
    if (task) {
        task.title = newTitle;
        saveTasks(tasks);
        renderAll();
    }
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

    // ダブルクリックで編集（PC）
    card.addEventListener('dblclick', (e: MouseEvent) => {
        if ((e.target as HTMLElement).closest('.kanban-task-delete')) return;
        startEdit(task, card);
    });

    // PC: HTML5 Drag & Drop
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);

    // モバイル: タッチイベント
    card.addEventListener('touchstart', handleTouchStart, { passive: false });
    card.addEventListener('touchmove', handleTouchMove, { passive: false });
    card.addEventListener('touchend', (e: TouchEvent) => {
        handleTouchEnd(e, task, card);
    }, { passive: false });

    return card;
}

// =========================================================
// インライン編集
// =========================================================

function startEdit(task: TempTask, card: HTMLElement): void {
    const textEl = card.querySelector('.kanban-task-text') as HTMLElement | null;
    if (!textEl) return;

    card.draggable = false;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = task.title;
    input.className = 'kanban-task-edit-input';

    let committed = false;

    function commit(): void {
        if (committed) return;
        committed = true;
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== task.title) {
            updateTask(task.id, newTitle);
        } else {
            renderAll();
        }
    }

    function cancel(): void {
        if (committed) return;
        committed = true;
        renderAll();
    }

    input.addEventListener('blur', commit);
    input.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            commit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancel();
        }
    });

    textEl.replaceWith(input);
    input.focus();
    input.select();
}

// =========================================================
// ドラッグオーバーレイ
// =========================================================

function showDragOverlay(): void {
    const overlay = document.getElementById('dragOverlay');
    if (overlay) overlay.classList.add('active');
}

function hideDragOverlay(): void {
    const overlay = document.getElementById('dragOverlay');
    if (overlay) {
        overlay.classList.remove('active');
        overlay.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-zone-hover'));
    }
}

function executeDragAction(action: string, taskId: string): void {
    switch (action) {
        case 'todo':
        case 'doing':
        case 'done':
            moveTask(taskId, action);
            break;
        case 'delete':
            deleteTask(taskId);
            break;
        default:
            renderAll();
    }
}

function initializeDragOverlay(): void {
    const overlay = document.getElementById('dragOverlay');
    if (!overlay) return;

    overlay.querySelectorAll<HTMLElement>('.drag-zone').forEach(zone => {
        zone.addEventListener('dragover', (e: DragEvent) => {
            e.preventDefault();
            if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
            overlay.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-zone-hover'));
            zone.classList.add('drag-zone-hover');
        });

        zone.addEventListener('dragleave', (e: DragEvent) => {
            if (zone.contains(e.relatedTarget as Node)) return;
            zone.classList.remove('drag-zone-hover');
        });

        zone.addEventListener('drop', (e: DragEvent) => {
            e.preventDefault();
            const action = zone.dataset.action || '';
            if (draggedTaskId) {
                executeDragAction(action, draggedTaskId);
            }
            hideDragOverlay();
        });
    });
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
    // ドラッグ画像キャプチャ後にオーバーレイ表示
    requestAnimationFrame(showDragOverlay);
}

function handleDragEnd(_e: DragEvent): void {
    if (dragSourceEl) dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedTaskId = null;
    hideDragOverlay();
}

// =========================================================
// モバイル タッチドラッグ
// =========================================================

function handleTouchStart(e: TouchEvent): void {
    if ((e.target as HTMLElement).closest('.kanban-task-delete')) return;

    const t = e.touches[0];
    const card = e.currentTarget as HTMLElement;
    touch.taskId = card.dataset.taskId || null;
    touch.startX = t.clientX;
    touch.startY = t.clientY;
    touch.sourceEl = card;
    touch.isDragging = false;
    touch.cloneEl = null;
    e.preventDefault();
}

function handleTouchMove(e: TouchEvent): void {
    if (!touch.taskId || !touch.sourceEl) return;

    const t = e.touches[0];
    const dx = t.clientX - touch.startX;
    const dy = t.clientY - touch.startY;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (!touch.isDragging) {
        if (dist < DRAG_THRESHOLD) return;
        touch.isDragging = true;

        const card = touch.sourceEl;
        const rect = card.getBoundingClientRect();
        const clone = card.cloneNode(true) as HTMLElement;
        clone.className = card.className + ' touch-clone';
        clone.style.width = rect.width + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.left = rect.left + 'px';
        document.body.appendChild(clone);
        touch.cloneEl = clone;
        card.style.opacity = '0.3';
        showDragOverlay();
    }

    e.preventDefault();
    if (!touch.cloneEl || !touch.sourceEl) return;

    const rect = touch.sourceEl.getBoundingClientRect();
    touch.cloneEl.style.left = (rect.left + dx) + 'px';
    touch.cloneEl.style.top = (rect.top + dy) + 'px';

    // ゾーンのハイライト
    const overlay = document.getElementById('dragOverlay');
    if (overlay && overlay.classList.contains('active')) {
        overlay.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-zone-hover'));
        touch.cloneEl.style.display = 'none';
        const elBelow = document.elementFromPoint(t.clientX, t.clientY);
        touch.cloneEl.style.display = '';
        const zone = elBelow && (elBelow as HTMLElement).closest<HTMLElement>('.drag-zone');
        if (zone) zone.classList.add('drag-zone-hover');
    }
}

function handleTouchEnd(e: TouchEvent, task: TempTask, card: HTMLElement): void {
    if (!touch.taskId) return;

    if (touch.isDragging) {
        if (touch.cloneEl) {
            document.body.removeChild(touch.cloneEl);
            touch.cloneEl = null;
        }
        if (touch.sourceEl) {
            touch.sourceEl.style.opacity = '';
            touch.sourceEl = null;
        }

        const t = e.changedTouches[0];
        const elBelow = document.elementFromPoint(t.clientX, t.clientY);
        const zone = elBelow && (elBelow as HTMLElement).closest<HTMLElement>('.drag-zone');
        if (zone && touch.taskId) {
            executeDragAction(zone.dataset.action || '', touch.taskId);
        } else {
            renderAll();
        }
        hideDragOverlay();
        touch.taskId = null;
        touch.isDragging = false;
    } else {
        // ダブルタップ検出
        const now = Date.now();
        if (now - lastTapTime < 300 && lastTapTaskId === task.id) {
            startEdit(task, card);
            lastTapTime = 0;
            lastTapTaskId = null;
        } else {
            lastTapTime = now;
            lastTapTaskId = task.id;
        }
        touch.taskId = null;
        touch.sourceEl = null;
    }
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
// 初期化
// =========================================================

function initializeInputs(): void {
    document.querySelectorAll<HTMLElement>('.kanban-input').forEach(el => {
        el.addEventListener('keypress', (e) => handleInputKeypress(e as KeyboardEvent));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeDragOverlay();
    initializeInputs();
    renderAll();
});
