// 一時タスク管理（カンバンボード）用 TypeScript
// サーバー側（DB）に非同期保存する実装

// app.ts で定義されたグローバル関数を参照
declare function getCookie(name: string): string | null;

// =========================================================
// 型定義
// =========================================================

interface TempTask {
    localId: string;          // クライアント側の一時ID（DOM操作用）
    serverId: number | null;  // サーバーDB上のID（null = 未保存）
    title: string;
    status: string;
    order: number;
    savedState: 'saved' | 'saving' | 'error';
}

// サーバーAPIレスポンスの型
interface ServerTask {
    id: number;
    title: string;
    status: string;
    order: number;
}

// セット
interface TempTaskSet {
    id: number;
    name: string;
    order: number;
}

let sets: TempTaskSet[] = [];
let currentSetId: number | null = null;
const SET_STORAGE_KEY = 'tempTaskCurrentSetId';

// ドラッグ状態管理
let draggedLocalId: string | null = null;
let dragSourceEl: HTMLElement | null = null;

// タッチドラッグ用状態管理
interface TouchState {
    localId: string | null;
    startX: number;
    startY: number;
    cloneEl: HTMLElement | null;
    sourceEl: HTMLElement | null;
    isDragging: boolean;
}

const touch: TouchState = {
    localId: null,
    startX: 0,
    startY: 0,
    cloneEl: null,
    sourceEl: null,
    isDragging: false,
};

// ダブルタップ検出用
let lastTapTime = 0;
let lastTapLocalId: string | null = null;

// 長押し検出用
let longPressTimerId: ReturnType<typeof setTimeout> | null = null;
let deletePendingLocalId: string | null = null;
let deleteModeAutoTimeoutId: ReturnType<typeof setTimeout> | null = null;

const DRAG_THRESHOLD = 8;       // px
const LONG_PRESS_DURATION = 500; // ms
const DELETE_MODE_TIMEOUT = 3000; // ms: 操作がなければ自動キャンセル

// =========================================================
// ローカル状態管理
// =========================================================

let tasks: TempTask[] = [];

function generateLocalId(): string {
    return 'local_' + Date.now().toString(36) + Math.random().toString(36).slice(2);
}

function getTaskByLocalId(localId: string): TempTask | undefined {
    return tasks.find(t => t.localId === localId);
}

function isDesktopLayout(): boolean {
    return window.innerWidth >= 768;
}

// =========================================================
// API ユーティリティ
// =========================================================

function tempTaskApiHeaders(): HeadersInit {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || '',
    };
}

function getApiBaseUrl(): string {
    const container = document.getElementById('tempTaskContainer');
    return container?.dataset.apiUrl || '';
}

function getApiClearUrl(): string {
    const container = document.getElementById('tempTaskContainer');
    return container?.dataset.apiClearUrl || '';
}

function getApiSetsUrl(): string {
    const container = document.getElementById('tempTaskContainer');
    return container?.dataset.apiSetsUrl || '';
}

function getApiSetDetailUrl(setId: number): string {
    const container = document.getElementById('tempTaskContainer');
    const base = container?.dataset.apiSetDetailBaseUrl || '';
    // base は /carbohydratepro/tasks/board/api/sets/0/ → 末尾の 0 を setId に置換
    return base.replace(/\/0\/$/, `/${setId}/`);
}

async function apiFetch(url: string, options: RequestInit): Promise<Response> {
    return fetch(url, { ...options, headers: tempTaskApiHeaders() });
}

async function apiGetTasks(): Promise<ServerTask[]> {
    const url = currentSetId !== null
        ? `${getApiBaseUrl()}?set_id=${currentSetId}`
        : getApiBaseUrl();
    const res = await fetch(url);
    if (!res.ok) throw new Error('タスク取得失敗');
    const data = await res.json() as { tasks: ServerTask[] };
    return data.tasks;
}

async function apiCreateTask(title: string, status: string): Promise<ServerTask> {
    const body: Record<string, unknown> = { title, status };
    if (currentSetId !== null) body.set_id = currentSetId;
    const res = await apiFetch(getApiBaseUrl(), {
        method: 'POST',
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error('タスク作成失敗');
    return res.json() as Promise<ServerTask>;
}

async function apiUpdateTask(serverId: number, updates: { title?: string; status?: string }): Promise<ServerTask> {
    const res = await apiFetch(`${getApiBaseUrl()}${serverId}/`, {
        method: 'PUT',
        body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error('タスク更新失敗');
    return res.json() as Promise<ServerTask>;
}

async function apiDeleteTask(serverId: number): Promise<void> {
    const res = await apiFetch(`${getApiBaseUrl()}${serverId}/`, {
        method: 'DELETE',
    });
    if (!res.ok) throw new Error('タスク削除失敗');
}

async function apiClearTasks(): Promise<void> {
    const body: Record<string, unknown> = {};
    if (currentSetId !== null) body.set_id = currentSetId;
    const res = await apiFetch(getApiClearUrl(), {
        method: 'DELETE',
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error('全削除失敗');
}

// =========================================================
// セット API
// =========================================================

async function apiGetSets(): Promise<TempTaskSet[]> {
    const res = await fetch(getApiSetsUrl());
    if (!res.ok) throw new Error('セット取得失敗');
    const data = await res.json() as { sets: TempTaskSet[] };
    return data.sets;
}

async function apiCreateSet(name: string): Promise<TempTaskSet> {
    const res = await apiFetch(getApiSetsUrl(), {
        method: 'POST',
        body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error('セット作成失敗');
    return res.json() as Promise<TempTaskSet>;
}

async function apiUpdateSet(setId: number, name: string): Promise<TempTaskSet> {
    const res = await apiFetch(getApiSetDetailUrl(setId), {
        method: 'PUT',
        body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error('セット更新失敗');
    return res.json() as Promise<TempTaskSet>;
}

async function apiDeleteSet(setId: number): Promise<void> {
    const res = await apiFetch(getApiSetDetailUrl(setId), { method: 'DELETE' });
    if (!res.ok) {
        const data = await res.json() as { error?: string };
        throw new Error(data.error || 'セット削除失敗');
    }
}

// =========================================================
// セット UI
// =========================================================

function renderSetTabs(): void {
    const container = document.getElementById('setTabs');
    if (!container) return;

    container.innerHTML = '';
    sets.forEach(s => {
        const tab = document.createElement('button');
        tab.className = 'set-tab' + (s.id === currentSetId ? ' active' : '');
        tab.dataset.setId = String(s.id);
        tab.textContent = s.name;
        tab.title = 'ダブルクリックでリネーム、長押しで削除';

        tab.addEventListener('click', () => {
            if (s.id !== currentSetId) void switchSet(s.id);
        });

        // ダブルクリックでリネーム
        tab.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            startRenameSet(tab, s.id, s.name);
        });

        // 長押しで削除（複数セットある場合のみ）
        let lpTimer: ReturnType<typeof setTimeout> | null = null;
        tab.addEventListener('mousedown', () => {
            if (sets.length <= 1) return;
            lpTimer = setTimeout(() => { void confirmDeleteSet(s.id, s.name); }, 700);
        });
        tab.addEventListener('mouseup', () => { if (lpTimer) clearTimeout(lpTimer); });
        tab.addEventListener('mouseleave', () => { if (lpTimer) clearTimeout(lpTimer); });
        tab.addEventListener('touchstart', () => {
            if (sets.length <= 1) return;
            lpTimer = setTimeout(() => { void confirmDeleteSet(s.id, s.name); }, 700);
        }, { passive: true });
        tab.addEventListener('touchend', () => { if (lpTimer) clearTimeout(lpTimer); });

        container.appendChild(tab);
    });
}

function startRenameSet(tab: HTMLButtonElement, setId: number, currentName: string): void {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'set-tab-input';
    input.value = currentName;
    input.maxLength = 50;

    tab.replaceWith(input);
    input.focus();
    input.select();

    const commit = (): void => {
        const newName = input.value.trim();
        if (newName && newName !== currentName) {
            void (async () => {
                try {
                    await apiUpdateSet(setId, newName);
                    const s = sets.find(x => x.id === setId);
                    if (s) s.name = newName;
                } catch { /* ignore */ }
                renderSetTabs();
            })();
        } else {
            renderSetTabs();
        }
    };

    input.addEventListener('blur', commit);
    input.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.key === 'Enter') { input.blur(); }
        if (e.key === 'Escape') { input.value = currentName; input.blur(); }
    });
}

async function confirmDeleteSet(setId: number, name: string): Promise<void> {
    if (sets.length <= 1) return;
    if (!confirm(`「${name}」を削除しますか？\nこのセットのタスクもすべて削除されます。`)) return;

    try {
        await apiDeleteSet(setId);
        sets = sets.filter(s => s.id !== setId);
        if (currentSetId === setId) {
            currentSetId = sets[0]?.id ?? null;
            if (currentSetId !== null) localStorage.setItem(SET_STORAGE_KEY, String(currentSetId));
        }
        tasks = [];
        renderSetTabs();
        renderAll();
        if (currentSetId !== null) await loadFromServer();
    } catch (err) {
        alert(err instanceof Error ? err.message : 'セット削除に失敗しました');
    }
}

async function switchSet(setId: number): Promise<void> {
    currentSetId = setId;
    localStorage.setItem(SET_STORAGE_KEY, String(setId));
    renderSetTabs();
    tasks = [];
    renderAll();
    await loadFromServer();
}

async function promptAddSet(): Promise<void> {
    const name = prompt('新しいセット名を入力してください（50文字以内）', '');
    if (!name || !name.trim()) return;
    try {
        const newSet = await apiCreateSet(name.trim());
        sets.push(newSet);
        await switchSet(newSet.id);
    } catch {
        alert('セットの作成に失敗しました');
    }
}

// =========================================================
// タスク操作（楽観的UI更新 + 非同期保存）
// =========================================================

async function addTask(status: string): Promise<void> {
    const input = document.getElementById(`input-${status}`) as HTMLInputElement | null;
    if (!input) return;
    const title = input.value.trim();
    if (!title) {
        input.focus();
        return;
    }

    const localId = generateLocalId();
    const newTask: TempTask = {
        localId,
        serverId: null,
        title,
        status,
        order: tasks.length,
        savedState: 'saving',
    };
    tasks.push(newTask);
    input.value = '';
    renderAll();
    input.focus();

    try {
        const saved = await apiCreateTask(title, status);
        const task = getTaskByLocalId(localId);
        if (task) {
            task.serverId = saved.id;
            task.savedState = 'saved';
            updateCardSavedState(localId);
        }
    } catch {
        const task = getTaskByLocalId(localId);
        if (task) {
            task.savedState = 'error';
            updateCardSavedState(localId);
        }
    }
}

async function deleteTask(localId: string): Promise<void> {
    const task = getTaskByLocalId(localId);
    if (!task) return;

    const serverId = task.serverId;
    tasks = tasks.filter(t => t.localId !== localId);
    renderAll();

    if (serverId !== null) {
        try {
            await apiDeleteTask(serverId);
        } catch {
            // 削除失敗は無視（UIからは消えている）
        }
    }
}

async function updateTask(localId: string, newTitle: string): Promise<void> {
    const task = getTaskByLocalId(localId);
    if (!task || !newTitle || newTitle === task.title) {
        renderAll();
        return;
    }

    task.title = newTitle;
    task.savedState = 'saving';
    renderAll();

    if (task.serverId !== null) {
        try {
            await apiUpdateTask(task.serverId, { title: newTitle });
            const t = getTaskByLocalId(localId);
            if (t) {
                t.savedState = 'saved';
                updateCardSavedState(localId);
            }
        } catch {
            const t = getTaskByLocalId(localId);
            if (t) {
                t.savedState = 'error';
                updateCardSavedState(localId);
            }
        }
    }
}

async function moveTask(localId: string, newStatus: string): Promise<void> {
    const task = getTaskByLocalId(localId);
    if (!task || task.status === newStatus) return;

    task.status = newStatus;
    task.savedState = 'saving';
    renderAll();

    if (task.serverId !== null) {
        try {
            await apiUpdateTask(task.serverId, { status: newStatus });
            const t = getTaskByLocalId(localId);
            if (t) {
                t.savedState = 'saved';
                updateCardSavedState(localId);
            }
        } catch {
            const t = getTaskByLocalId(localId);
            if (t) {
                t.savedState = 'error';
                updateCardSavedState(localId);
            }
        }
    }
}

async function clearAllTasks(): Promise<void> {
    if (!confirm('すべてのタスクを削除してもよろしいですか？')) return;

    const hasServerTasks = tasks.some(t => t.serverId !== null);
    tasks = [];
    renderAll();

    if (hasServerTasks) {
        try {
            await apiClearTasks();
        } catch {
            // 失敗は無視
        }
    }
}

// =========================================================
// 初期ロード（サーバーからデータ取得）
// =========================================================

async function loadFromServer(): Promise<void> {
    try {
        const serverTasks = await apiGetTasks();
        tasks = serverTasks.map(st => ({
            localId: generateLocalId(),
            serverId: st.id,
            title: st.title,
            status: st.status,
            order: st.order,
            savedState: 'saved' as const,
        }));
        renderAll();
    } catch {
        tasks = [];
        renderAll();
    }
}

async function initSets(): Promise<void> {
    try {
        sets = await apiGetSets();
    } catch {
        sets = [];
    }

    // localStorage から前回のセットIDを復元
    const saved = localStorage.getItem(SET_STORAGE_KEY);
    const savedId = saved ? parseInt(saved, 10) : NaN;
    if (!isNaN(savedId) && sets.some(s => s.id === savedId)) {
        currentSetId = savedId;
    } else if (sets.length > 0) {
        currentSetId = sets[0].id;
    }

    renderSetTabs();
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

    const columnTasks = tasks.filter(t => t.status === status);
    container.innerHTML = '';
    columnTasks.forEach(task => container.appendChild(createTaskCard(task)));

    if (countEl) countEl.textContent = String(columnTasks.length);
}

function renderAll(): void {
    renderColumn('todo');
    renderColumn('doing');
    renderColumn('done');
}

function updateCardSavedState(localId: string): void {
    const card = document.querySelector<HTMLElement>(`[data-local-id="${CSS.escape(localId)}"]`);
    const task = getTaskByLocalId(localId);
    if (!card || !task) return;

    card.classList.remove('saving', 'save-error');
    if (task.savedState === 'saving') {
        card.classList.add('saving');
    } else if (task.savedState === 'error') {
        card.classList.add('save-error');
    }

    // 未保存ドットを更新
    const dot = card.querySelector<HTMLElement>('.kanban-task-unsaved-dot');
    if (task.savedState !== 'saved') {
        if (!dot) {
            const newDot = document.createElement('span');
            newDot.className = 'kanban-task-unsaved-dot';
            newDot.title = task.savedState === 'error' ? '保存失敗' : '保存中...';
            const deleteOverlay = card.querySelector('.kanban-task-delete-overlay');
            if (deleteOverlay) card.insertBefore(newDot, deleteOverlay);
        } else {
            dot.title = task.savedState === 'error' ? '保存失敗' : '保存中...';
        }
    } else {
        dot?.remove();
    }
}

function createTaskCard(task: TempTask): HTMLElement {
    const card = document.createElement('div');
    card.className = 'kanban-task-card';
    if (task.savedState === 'saving') card.classList.add('saving');
    if (task.savedState === 'error') card.classList.add('save-error');
    card.dataset.localId = task.localId;
    card.draggable = true;

    const unsavedIndicator = task.savedState !== 'saved'
        ? `<span class="kanban-task-unsaved-dot" title="${task.savedState === 'error' ? '保存失敗' : '保存中...'}"></span>`
        : '';

    card.innerHTML = `
        <span class="kanban-task-text">${escapeHtml(task.title)}</span>
        ${unsavedIndicator}
        <div class="kanban-task-delete-overlay" title="削除">
            <i class="fas fa-trash-alt"></i>
        </div>
    `;

    // 削除オーバーレイ（長押し後に表示）のクリックで削除
    const deleteOverlay = card.querySelector<HTMLElement>('.kanban-task-delete-overlay');
    if (deleteOverlay) {
        deleteOverlay.addEventListener('click', (e) => {
            e.stopPropagation();
            deactivateDeleteMode();
            void deleteTask(task.localId);
        });
        // タッチ時にカードのタッチハンドラへの伝播を防ぐ
        deleteOverlay.addEventListener('touchstart', (e) => { e.stopPropagation(); }, { passive: false });
        deleteOverlay.addEventListener('touchend', (e) => { e.stopPropagation(); }, { passive: false });
    }

    // ダブルクリックで編集（PC）
    card.addEventListener('dblclick', (e: MouseEvent) => {
        if ((e.target as HTMLElement).closest('.kanban-task-delete-overlay')) return;
        if (deletePendingLocalId === task.localId) {
            deactivateDeleteMode();
            return;
        }
        startEdit(task, card);
    });

    // PC: 長押し検出（mousedown/mouseup/mouseleave）
    card.addEventListener('mousedown', (e: MouseEvent) => {
        if (e.button !== 0) return;
        if ((e.target as HTMLElement).closest('.kanban-task-delete-overlay')) return;
        if (deletePendingLocalId) {
            deactivateDeleteMode();
            return;
        }
        startLongPressTimer(task.localId);
    });
    card.addEventListener('mouseup', cancelLongPressTimer);
    card.addEventListener('mouseleave', cancelLongPressTimer);

    // PC: HTML5 Drag & Drop
    card.addEventListener('dragstart', (e: DragEvent) => {
        cancelLongPressTimer();
        handleDragStart(e);
    });
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
// 長押し削除モード
// =========================================================

function startLongPressTimer(localId: string): void {
    cancelLongPressTimer();
    longPressTimerId = setTimeout(() => {
        activateDeleteMode(localId);
    }, LONG_PRESS_DURATION);
}

function cancelLongPressTimer(): void {
    if (longPressTimerId !== null) {
        clearTimeout(longPressTimerId);
        longPressTimerId = null;
    }
}

function activateDeleteMode(localId: string): void {
    deactivateDeleteMode();

    const card = document.querySelector<HTMLElement>(`[data-local-id="${CSS.escape(localId)}"]`);
    if (!card) return;

    deletePendingLocalId = localId;
    card.classList.add('delete-pending');
    card.draggable = false;

    // 軽いバイブレーションフィードバック（対応端末のみ）
    if (navigator.vibrate) navigator.vibrate(40);

    // 3秒後に自動キャンセル
    deleteModeAutoTimeoutId = setTimeout(deactivateDeleteMode, DELETE_MODE_TIMEOUT);

    // カード外クリックでキャンセル
    setTimeout(() => {
        document.addEventListener('click', handleOutsideClickForDeleteMode, { once: true });
    }, 0);
}

function deactivateDeleteMode(): void {
    if (deleteModeAutoTimeoutId !== null) {
        clearTimeout(deleteModeAutoTimeoutId);
        deleteModeAutoTimeoutId = null;
    }
    if (!deletePendingLocalId) return;

    const card = document.querySelector<HTMLElement>(`[data-local-id="${CSS.escape(deletePendingLocalId)}"]`);
    if (card) {
        card.classList.remove('delete-pending');
        card.draggable = true;
    }
    deletePendingLocalId = null;
}

function handleOutsideClickForDeleteMode(e: Event): void {
    const target = e.target as HTMLElement;
    if (!target.closest('.kanban-task-delete-overlay')) {
        deactivateDeleteMode();
    }
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
            void updateTask(task.localId, newTitle);
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
// PC ドラッグ & ドロップ（デスクトップ: カラム直接ドロップ）
// =========================================================

function showDeleteZone(): void {
    const zone = document.getElementById('kanbanDeleteZone');
    if (zone) zone.classList.add('active');
}

function hideDeleteZone(): void {
    const zone = document.getElementById('kanbanDeleteZone');
    if (zone) zone.classList.remove('active', 'drag-over');
}

function initializeDeleteZone(): void {
    const zone = document.getElementById('kanbanDeleteZone');
    if (!zone) return;

    zone.addEventListener('dragover', (e: DragEvent) => {
        e.preventDefault();
        if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', (e: DragEvent) => {
        if (zone.contains(e.relatedTarget as Node)) return;
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e: DragEvent) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (draggedLocalId) {
            void deleteTask(draggedLocalId);
        }
        hideDeleteZone();
    });
}

function initializeColumnDropZones(): void {
    document.querySelectorAll<HTMLElement>('.kanban-tasks').forEach(col => {
        col.addEventListener('dragover', (e: DragEvent) => {
            if (!isDesktopLayout()) return;
            e.preventDefault();
            if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
            col.classList.add('drag-over');
        });

        col.addEventListener('dragleave', (e: DragEvent) => {
            if (col.contains(e.relatedTarget as Node)) return;
            col.classList.remove('drag-over');
        });

        col.addEventListener('drop', (e: DragEvent) => {
            e.preventDefault();
            col.classList.remove('drag-over');
            if (!isDesktopLayout()) return;
            const status = col.dataset.status || '';
            if (draggedLocalId && status) {
                void moveTask(draggedLocalId, status);
            }
        });
    });
}

function handleDragStart(e: DragEvent): void {
    dragSourceEl = e.currentTarget as HTMLElement;
    draggedLocalId = dragSourceEl.dataset.localId || null;
    dragSourceEl.classList.add('dragging');
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedLocalId || '');
    }
    requestAnimationFrame(() => {
        if (isDesktopLayout()) {
            showDeleteZone();
        } else {
            showDragOverlay();
        }
    });
}

function handleDragEnd(_e: DragEvent): void {
    if (dragSourceEl) dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedLocalId = null;
    hideDragOverlay();
    hideDeleteZone();
    document.querySelectorAll('.kanban-tasks').forEach(c => c.classList.remove('drag-over'));
}

// =========================================================
// ドラッグオーバーレイ（モバイル用5ゾーン）
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

function executeDragAction(action: string, localId: string): void {
    switch (action) {
        case 'todo':
        case 'doing':
        case 'done':
            void moveTask(localId, action);
            break;
        case 'delete':
            void deleteTask(localId);
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
            if (draggedLocalId) {
                executeDragAction(action, draggedLocalId);
            }
            hideDragOverlay();
        });
    });
}

// =========================================================
// モバイル タッチドラッグ
// =========================================================

function handleTouchStart(e: TouchEvent): void {
    // 削除オーバーレイのタッチはカードハンドラに流さない
    if ((e.target as HTMLElement).closest('.kanban-task-delete-overlay')) return;

    // 削除モード中は一旦キャンセル
    if (deletePendingLocalId) {
        deactivateDeleteMode();
        return;
    }

    const t = e.touches[0];
    const card = e.currentTarget as HTMLElement;
    touch.localId = card.dataset.localId || null;
    touch.startX = t.clientX;
    touch.startY = t.clientY;
    touch.sourceEl = card;
    touch.isDragging = false;
    touch.cloneEl = null;
    e.preventDefault();

    // 長押しタイマー開始
    if (touch.localId) {
        startLongPressTimer(touch.localId);
    }
}

function handleTouchMove(e: TouchEvent): void {
    if (!touch.localId || !touch.sourceEl) return;

    const t = e.touches[0];
    const dx = t.clientX - touch.startX;
    const dy = t.clientY - touch.startY;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (!touch.isDragging) {
        if (dist < DRAG_THRESHOLD) return;
        // ドラッグ開始 → 長押しキャンセル
        cancelLongPressTimer();
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
    touch.cloneEl.style.left = (rect.left + (t.clientX - touch.startX)) + 'px';
    touch.cloneEl.style.top = (rect.top + (t.clientY - touch.startY)) + 'px';

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
    cancelLongPressTimer();

    if (!touch.localId) return;

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
        if (zone && touch.localId) {
            executeDragAction(zone.dataset.action || '', touch.localId);
        } else {
            renderAll();
        }
        hideDragOverlay();
        touch.localId = null;
        touch.isDragging = false;
    } else {
        // 長押し中（delete-pending）の場合はダブルタップを無視
        if (deletePendingLocalId === task.localId) {
            touch.localId = null;
            touch.sourceEl = null;
            return;
        }

        // ダブルタップ検出
        const now = Date.now();
        if (now - lastTapTime < 300 && lastTapLocalId === task.localId) {
            startEdit(task, card);
            lastTapTime = 0;
            lastTapLocalId = null;
        } else {
            lastTapTime = now;
            lastTapLocalId = task.localId;
        }
        touch.localId = null;
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
        void addTask(input.dataset.status || '');
    }
}

// =========================================================
// リトライ
// =========================================================

const RETRY_INTERVAL_MS = 30_000;

async function retryFailedTasks(): Promise<void> {
    const failedTasks = tasks.filter(t => t.savedState === 'error');
    if (failedTasks.length === 0) return;

    for (const task of failedTasks) {
        if (!getTaskByLocalId(task.localId)) continue;

        task.savedState = 'saving';
        updateCardSavedState(task.localId);

        try {
            if (task.serverId === null) {
                const saved = await apiCreateTask(task.title, task.status);
                const t = getTaskByLocalId(task.localId);
                if (t) {
                    t.serverId = saved.id;
                    t.savedState = 'saved';
                    updateCardSavedState(t.localId);
                }
            } else {
                await apiUpdateTask(task.serverId, { title: task.title, status: task.status });
                const t = getTaskByLocalId(task.localId);
                if (t) {
                    t.savedState = 'saved';
                    updateCardSavedState(t.localId);
                }
            }
        } catch {
            const t = getTaskByLocalId(task.localId);
            if (t) {
                t.savedState = 'error';
                updateCardSavedState(t.localId);
            }
        }
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
    initializeDeleteZone();
    initializeColumnDropZones();
    initializeInputs();
    void (async () => {
        await initSets();
        await loadFromServer();
    })();

    // Escape キーで削除モードキャンセル
    document.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.key === 'Escape' && deletePendingLocalId) {
            deactivateDeleteMode();
        }
    });

    // 定期リトライ
    setInterval(() => { void retryFailedTasks(); }, RETRY_INTERVAL_MS);

    // ネットワーク復帰時に即リトライ
    window.addEventListener('online', () => { void retryFailedTasks(); });

    // タブ再表示時に即リトライ
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            void retryFailedTasks();
        }
    });
});
