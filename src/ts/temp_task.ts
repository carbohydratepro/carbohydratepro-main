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

interface DeleteReceipt {
    restore_url: string;
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


// 長押し検出用
let longPressTimerId: ReturnType<typeof setTimeout> | null = null;
let deletePendingLocalId: string | null = null;
let deleteModeAutoTimeoutId: ReturnType<typeof setTimeout> | null = null;

const LONG_PRESS_DURATION = 500; // ms
const DELETE_MODE_TIMEOUT = 3000; // ms: 操作がなければ自動キャンセル

// =========================================================
// ローカル状態管理
// =========================================================

let tasks: TempTask[] = [];

let boardLoading = true;
let boardLoadVersion = 0;
let boardMutation = false;
let boardSelectedTask: string | null = null;
let boardRenameSet = false;
let boardReturnFocus: HTMLElement | null = null;

function boardFeedback(message: string): void {
    const status = document.getElementById('boardFeedback');
    if (status) status.textContent = message;
}

function boardCanLeave(): boolean {
    if (boardMutation || tasks.some(t => t.savedState !== 'saved')) {
        showToast('保存中、または未保存のタスクがあります。保存を完了してから操作してください。', 'info');
        return false;
    }
    return true;
}

function boardRefreshControls(): void {
    document.getElementById('boardSaveRetry')!.hidden = !tasks.some(t => t.savedState === 'error');
    document.querySelectorAll<HTMLInputElement | HTMLButtonElement>('.kanban-input, .kanban-add-btn').forEach(el => {
        el.disabled = boardLoading || boardMutation || currentSetId === null || !document.getElementById('boardRetry')!.hidden;
    });
    document.querySelectorAll<HTMLButtonElement>('.set-tab, .set-add-btn').forEach(el => {
        el.disabled = boardMutation || tasks.some(t => t.savedState !== 'saved');
    });
    document.querySelectorAll<HTMLElement>('.kanban-task-card').forEach(card => {
        const task = getTaskByLocalId(card.dataset.localId || '');
        card.querySelectorAll<HTMLButtonElement>('.board-card-action').forEach(button => { button.disabled = boardMutation || task?.savedState !== 'saved'; });
    });
}

function openBoardSheet(id: string): void {
    boardReturnFocus = document.activeElement as HTMLElement;
    (document.getElementById(id) as HTMLDialogElement).showModal();
    document.body.classList.add('board-sheet-open');
}

function openBoardTaskEditor(localId: string): void {
    const task = getTaskByLocalId(localId);
    if (!task || task.savedState !== 'saved' || boardMutation) return;
    boardSelectedTask = localId;
    (document.getElementById('boardTaskTitle') as HTMLTextAreaElement).value = task.title;
    (document.getElementById('boardTaskStatus') as HTMLSelectElement).value = task.status;
    document.getElementById('boardTaskError')!.textContent = '';
    openBoardSheet('boardTaskSheet');
}

function openBoardSetEditor(rename: boolean): void {
    if (!boardCanLeave() || boardLoading) return;
    boardRenameSet = rename;
    const current = sets.find(s => s.id === currentSetId);
    if (rename && !current) return;
    document.getElementById('boardSetSheetTitle')!.textContent = rename ? 'セット名を変更' : 'セットを追加';
    (document.getElementById('boardSetName') as HTMLInputElement).value = rename ? current!.name : '';
    document.getElementById('boardSetError')!.textContent = '';
    openBoardSheet('boardSetSheet');
}

function deleteCurrentBoardSet(): void {
    if (!boardCanLeave() || boardLoading) return;
    const current = sets.find(s => s.id === currentSetId);
    if (sets.length <= 1) { showToast('最後のセットは削除できません。', 'info'); return; }
    if (current) confirmDeleteSet(current.id, current.name);
}

function boardSheetBusy(sheet: HTMLDialogElement, busy: boolean): void {
    boardMutation = busy;
    sheet.setAttribute('aria-busy', String(busy));
    sheet.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>('button, input, textarea, select').forEach(el => { el.disabled = busy; });
    boardRefreshControls();
}

function initializeBoardExperience(): void {
    document.getElementById('tempTaskContainer')!.dataset.activeStatus = 'todo';
    document.querySelectorAll<HTMLButtonElement>('[data-board-status]').forEach(button => {
        button.addEventListener('click', () => {
            document.getElementById('tempTaskContainer')!.dataset.activeStatus = button.dataset.boardStatus;
            document.querySelectorAll('[data-board-status]').forEach(peer => peer.setAttribute('aria-pressed', String(peer === button)));
        });
    });
    document.querySelectorAll<HTMLInputElement>('.kanban-input').forEach(input => { input.maxLength = 200; input.enterKeyHint = 'done'; });
    document.querySelectorAll<HTMLDialogElement>('.board-sheet').forEach(sheet => {
        sheet.addEventListener('cancel', event => { if (boardMutation) event.preventDefault(); });
        sheet.addEventListener('close', () => {
            document.body.classList.remove('board-sheet-open');
            if (boardReturnFocus?.isConnected) boardReturnFocus.focus();
            else document.querySelector<HTMLButtonElement>('[data-board-status][aria-pressed="true"]')?.focus();
        });
        sheet.querySelectorAll('[data-close-board-sheet]').forEach(button => button.addEventListener('click', () => { if (!boardMutation) sheet.close(); }));
    });
    document.getElementById('boardRetry')!.addEventListener('click', () => {
        void (async () => {
            if (currentSetId === null) await initSets();
            if (currentSetId !== null) await loadFromServer();
        })();
    });
    document.getElementById('boardSaveRetry')!.addEventListener('click', () => { void retryFailedTasks(); });
    window.addEventListener('beforeunload', event => {
        if (boardMutation || tasks.some(t => t.savedState !== 'saved')) { event.preventDefault(); event.returnValue = ''; }
    });
    document.getElementById('boardTaskForm')!.addEventListener('submit', event => {
        event.preventDefault();
        void (async () => {
            const task = boardSelectedTask ? getTaskByLocalId(boardSelectedTask) : undefined;
            if (!task || task.serverId === null || boardMutation) return;
            const title = (document.getElementById('boardTaskTitle') as HTMLTextAreaElement).value.trim();
            const status = (document.getElementById('boardTaskStatus') as HTMLSelectElement).value;
            if (!title) { document.getElementById('boardTaskError')!.textContent = 'タスク名を入力してください。'; return; }
            const sheet = document.getElementById('boardTaskSheet') as HTMLDialogElement;
            boardSheetBusy(sheet, true);
            try {
                const saved = await apiUpdateTask(task.serverId, { title, status });
                task.title = saved.title;
                task.status = saved.status;
                renderAll();
                sheet.close();
                boardFeedback('保存しました。');
            } catch (error) {
                if (error instanceof Error && error.message === 'demo') sheet.close();
                else document.getElementById('boardTaskError')!.textContent = '保存できませんでした。入力は保持しています。もう一度保存してください。';
            } finally { boardSheetBusy(sheet, false); }
        })();
    });
    document.getElementById('boardTaskDelete')!.addEventListener('click', () => {
        if (boardMutation || !boardSelectedTask) return;
        (document.getElementById('boardTaskSheet') as HTMLDialogElement).close();
        deleteTask(boardSelectedTask);
    });
    document.getElementById('boardSetForm')!.addEventListener('submit', event => {
        event.preventDefault();
        void (async () => {
            if (boardMutation) return;
            const name = (document.getElementById('boardSetName') as HTMLInputElement).value.trim();
            if (!name) return;
            const sheet = document.getElementById('boardSetSheet') as HTMLDialogElement;
            boardSheetBusy(sheet, true);
            try {
                if (boardRenameSet && currentSetId !== null) {
                    await apiUpdateSet(currentSetId, name);
                    sets.find(s => s.id === currentSetId)!.name = name;
                } else {
                    const set = await apiCreateSet(name);
                    sets.push(set);
                    currentSetId = set.id;
                    localStorage.setItem(SET_STORAGE_KEY, String(set.id));
                    tasks = [];
                    renderAll();
                }
                renderSetTabs();
                sheet.close();
                boardFeedback('セットを保存しました。');
            } catch (error) {
                if (error instanceof Error && error.message === 'demo') sheet.close();
                else document.getElementById('boardSetError')!.textContent = '保存できませんでした。もう一度お試しください。';
            } finally { boardSheetBusy(sheet, false); }
        })();
    });
}

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
        'X-Requested-With': 'XMLHttpRequest',
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

async function apiDeleteTask(serverId: number): Promise<DeleteReceipt> {
    // keepalive: 削除直後にページを離脱してもリクエストを送り切る
    const res = await apiFetch(`${getApiBaseUrl()}${serverId}/`, {
        method: 'DELETE',
        keepalive: true,
    });
    if (!res.ok) throw new Error('タスク削除失敗');
    return res.json() as Promise<DeleteReceipt>;
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
        tab.setAttribute('aria-pressed', String(s.id === currentSetId));

        tab.addEventListener('click', () => {
            if (s.id !== currentSetId) void switchSet(s.id);
        });

        container.appendChild(tab);
    });
}


function confirmDeleteSet(setId: number, name: string): void {
    if (sets.length <= 1) return;
    showConfirm({
        message: `「${name}」を削除しますか？\nこのセットのタスクもすべて削除されます。`,
        confirmLabel: '削除',
        danger: true,
        onConfirm: () => { void deleteSet(setId); },
    });
}

async function deleteSet(setId: number): Promise<void> {
    if (!boardCanLeave()) return;
    boardMutation = true;
    boardRefreshControls();
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
        showToast('セットを削除しました。ごみ箱から元に戻せます。', 'success');
    } catch (err) {
        showToast(err instanceof Error ? err.message : 'セット削除に失敗しました', 'error');
    } finally {
        boardMutation = false;
        boardRefreshControls();
    }
}

async function switchSet(setId: number): Promise<void> {
    if (!boardCanLeave()) return;
    currentSetId = setId;
    localStorage.setItem(SET_STORAGE_KEY, String(setId));
    renderSetTabs();
    tasks = [];
    renderAll();
    await loadFromServer();
}

async function promptAddSet(): Promise<void> {
    openBoardSetEditor(false);
}

// =========================================================
// タスク操作（楽観的UI更新 + 非同期保存）
// =========================================================

async function addTask(status: string): Promise<void> {
    if (boardLoading || currentSetId === null) return;
    const input = document.getElementById(`input-${status}`) as HTMLInputElement | null;
    if (!input) return;
    const title = input.value.trim();
    if (title.length > 200) { showToast('タスク名は200文字以内で入力してください。', 'error'); return; }
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
    } catch (error) {
        const task = getTaskByLocalId(localId);
        if (task) {
            if (error instanceof Error && error.message === 'demo') {
                tasks = tasks.filter(t => t.localId !== localId);
                renderAll();
                return;
            }
            task.savedState = 'error';
            updateCardSavedState(localId);
            boardFeedback('保存できませんでした。この画面を開いたまま再試行してください。');
        }
    }
}

async function deleteTask(localId: string): Promise<void> {
    const index = tasks.findIndex(t => t.localId === localId);
    if (index === -1) return;
    const task = tasks[index];
    if (task.savedState !== 'saved' || boardMutation) return;
    const setId = currentSetId;
    boardMutation = true;
    boardRefreshControls();
    let receipt: DeleteReceipt;
    try {
        if (task.serverId === null) return;
        receipt = await apiDeleteTask(task.serverId);
    } catch (error) {
        if (!(error instanceof Error && error.message === 'demo')) showToast('削除できませんでした。タスクは残しています。', 'error');
        return;
    } finally { boardMutation = false; boardRefreshControls(); }

    // UIから消し、サーバー側では削除履歴へ保存する。Undoでは同じデータを復元する。
    tasks.splice(index, 1);
    renderAll();

    const shortTitle = task.title.length > 20 ? task.title.slice(0, 20) + '…' : task.title;
    showUndoToast({
        message: `「${shortTitle}」を削除しました`,
        onUndo: () => { void (async () => {
            try {
                const response = await apiFetch(receipt.restore_url, { method: 'POST' });
                if (!response.ok) throw new Error('restore');
                if (currentSetId === setId) {
                    tasks.splice(Math.min(index, tasks.length), 0, task);
                    renderAll();
                }
                showToast('元に戻しました。', 'success');
            } catch { showToast('復元できませんでした。ごみ箱から復元してください。', 'error'); }
        })(); },
        onCommit: () => { /* 既に削除済み。確定時は何もしない */ },
    });
}

// 削除履歴から同じIDのタスクを復元する（Undo用）

async function moveTask(localId: string, newStatus: string): Promise<void> {
    const task = getTaskByLocalId(localId);
    if (!task || task.status === newStatus || task.savedState !== 'saved' || boardMutation) return;

    const oldStatus = task.status;
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
        } catch (error) {
            const t = getTaskByLocalId(localId);
            if (t) {
                if (error instanceof Error && error.message === 'demo') {
                    t.status = oldStatus;
                    t.savedState = 'saved';
                    renderAll();
                    return;
                }
                t.savedState = 'error';
                updateCardSavedState(localId);
            }
        }
    }
}

function clearAllTasks(): void {
    if (!boardCanLeave()) return;
    if (tasks.length === 0) return;
    showConfirm({
        message: 'このセットのタスクをすべて削除しますか？',
        confirmLabel: 'すべて削除',
        danger: true,
        onConfirm: () => { void runClearAllTasks(); },
    });
}

async function runClearAllTasks(): Promise<void> {
    if (!boardCanLeave()) return;
    boardMutation = true;
    boardRefreshControls();
    try {
        await apiClearTasks();
        tasks = [];
        renderAll();
        showToast('削除しました。ごみ箱から元に戻せます。', 'success');
    } catch { showToast('削除できませんでした。タスクは残しています。', 'error'); }
    finally { boardMutation = false; boardRefreshControls(); }
}

// =========================================================
// 初期ロード（サーバーからデータ取得）
// =========================================================

async function loadFromServer(): Promise<void> {
    const requestId = ++boardLoadVersion;
    boardLoading = true;
    document.getElementById('boardRetry')!.hidden = true;
    boardFeedback('読み込んでいます…');
    boardRefreshControls();
    try {
        const serverTasks = await apiGetTasks();
        if (requestId !== boardLoadVersion) return;
        tasks = serverTasks.map(st => ({
            localId: generateLocalId(),
            serverId: st.id,
            title: st.title,
            status: st.status,
            order: st.order,
            savedState: 'saved' as const,
        }));
        renderAll();
        boardFeedback('');
    } catch {
        if (requestId !== boardLoadVersion) return;
        boardFeedback('読み込めませんでした。通信を確認して再試行してください。');
        document.getElementById('boardRetry')!.hidden = false;
        return;
    } finally {
        if (requestId === boardLoadVersion) {
            boardLoading = false;
            boardRefreshControls();
        }
    }
}

async function initSets(): Promise<void> {
    try {
        sets = await apiGetSets();
    } catch {
        sets = [];
        boardLoading = false;
        boardFeedback('セットを読み込めませんでした。通信を確認して再試行してください。');
        document.getElementById('boardRetry')!.hidden = false;
        boardRefreshControls();
        return;
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
    if (!columnTasks.length) {
        const empty = document.createElement('p');
        empty.className = 'board-empty';
        empty.textContent = status === 'done' ? '完了したタスクがここに並びます' : 'まだタスクはありません';
        container.appendChild(empty);
    }
    const filterCount = document.getElementById(`filter-count-${status}`);
    if (filterCount) filterCount.textContent = String(columnTasks.length);

    if (countEl) countEl.textContent = String(columnTasks.length);
}

function renderAll(): void {
    const focused = document.activeElement as HTMLElement | null;
    const focusedCard = focused?.closest<HTMLElement>('.kanban-task-card');
    const focusedId = focusedCard?.dataset.localId;
    const wasComplete = focused?.classList.contains('board-complete');
    renderColumn('todo');
    renderColumn('doing');
    renderColumn('done');
    const done = tasks.filter(t => t.status === 'done').length;
    document.getElementById('boardProgressText')!.textContent = tasks.length ? `${tasks.length}件のうち ${done}件が完了` : '頭の中の「やること」を、ここに。';
    const progress = document.getElementById('boardProgress') as HTMLProgressElement;
    progress.max = tasks.length || 1;
    progress.value = done;
    boardRefreshControls();
    if (focusedId) {
        const replacement = document.querySelector<HTMLElement>(`[data-local-id="${CSS.escape(focusedId)}"] ${wasComplete ? '.board-complete' : '.kanban-task-text'}`);
        const fallback = window.innerWidth < 768
            ? document.querySelector<HTMLElement>('[data-board-status][aria-pressed="true"]')
            : document.getElementById('input-todo');
        (replacement?.getClientRects().length ? replacement : fallback)?.focus({ preventScroll: true });
    }
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
    card.querySelectorAll<HTMLButtonElement>('.board-card-action').forEach(button => { button.disabled = task.savedState !== 'saved'; });
    card.draggable = task.savedState === 'saved' && !window.matchMedia('(pointer: coarse)').matches;
    boardRefreshControls();
}

function createTaskCard(task: TempTask): HTMLElement {
    const card = document.createElement('div');
    card.className = 'kanban-task-card';
    if (task.savedState === 'saving') card.classList.add('saving');
    if (task.savedState === 'error') card.classList.add('save-error');
    card.dataset.localId = task.localId;
    card.draggable = task.savedState === 'saved' && !window.matchMedia('(pointer: coarse)').matches;

    const unsavedIndicator = task.savedState !== 'saved'
        ? `<span class="kanban-task-unsaved-dot" title="${task.savedState === 'error' ? '保存失敗' : '保存中...'}"></span>`
        : '';

    card.innerHTML = `
        <button type="button" class="board-card-action board-complete" aria-label="${task.status === 'done' ? '未完了に戻す' : '完了にする'}" ${task.savedState !== 'saved' ? 'disabled' : ''}><i class="${task.status === 'done' ? 'fas fa-check-circle' : 'far fa-circle'}" aria-hidden="true"></i></button>
        <button type="button" class="board-card-action kanban-task-text" ${task.savedState !== 'saved' ? 'disabled' : ''}>${escapeHtml(task.title)}</button>
        ${unsavedIndicator}
        <button type="button" class="kanban-task-delete-overlay" aria-label="「${escapeHtml(task.title)}」を削除" title="削除">
            <i class="fas fa-trash-alt" aria-hidden="true"></i> 削除
        </button>
    `;
    card.querySelector('.kanban-task-text')!.addEventListener('click', () => openBoardTaskEditor(task.localId));
    card.querySelector('.board-complete')!.addEventListener('click', () => {
        void moveTask(task.localId, task.status === 'done' ? 'todo' : 'done').then(() => boardFeedback(task.savedState === 'saved' ? '状態を更新しました。' : '保存できませんでした。再試行してください。'));
    });

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
        if ((e.target as HTMLElement).closest('button, input, textarea')) return;
        if (deletePendingLocalId === task.localId) {
            deactivateDeleteMode();
            return;
        }
        openBoardTaskEditor(task.localId);
    });

    // PC: 長押し検出（mousedown/mouseup/mouseleave）
    card.addEventListener('mousedown', (e: MouseEvent) => {
        if (e.button !== 0) return;
        if ((e.target as HTMLElement).closest('button, input, textarea') || window.matchMedia('(pointer: coarse)').matches) return;
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

    // タッチはブラウザのスクロール・ズームへ委ねる。操作は明示的なボタンから。

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
    if (!isDesktopLayout() || window.matchMedia('(pointer: coarse)').matches || !boardCanLeave()) { e.preventDefault(); return; }
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
        }
    });
}

function handleDragEnd(_e: DragEvent): void {
    if (dragSourceEl) dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedLocalId = null;
    hideDeleteZone();
    document.querySelectorAll('.kanban-tasks').forEach(c => c.classList.remove('drag-over'));
}

// =========================================================
// ドラッグオーバーレイ（モバイル用5ゾーン）
// =========================================================


function handleInputKeypress(e: KeyboardEvent): void {
    if (e.key === 'Enter' && !e.isComposing) {
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
    boardFeedback(tasks.some(t => t.savedState === 'error') ? '保存できませんでした。通信を確認して再試行してください。' : '保存しました。');
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
    initializeBoardExperience();
    initializeDeleteZone();
    initializeColumnDropZones();
    initializeInputs();
    void (async () => {
        await initSets();
        if (currentSetId !== null) await loadFromServer();
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
