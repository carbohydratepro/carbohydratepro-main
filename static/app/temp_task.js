"use strict";
// 一時タスク管理（カンバンボード）用 TypeScript
// サーバー側（DB）に非同期保存する実装
// ドラッグ状態管理
let draggedLocalId = null;
let dragSourceEl = null;
const touch = {
    localId: null,
    startX: 0,
    startY: 0,
    cloneEl: null,
    sourceEl: null,
    isDragging: false,
};
// ダブルタップ検出用
let lastTapTime = 0;
let lastTapLocalId = null;
const DRAG_THRESHOLD = 8; // px
// =========================================================
// ローカル状態管理
// =========================================================
let tasks = [];
function generateLocalId() {
    return 'local_' + Date.now().toString(36) + Math.random().toString(36).slice(2);
}
function getTaskByLocalId(localId) {
    return tasks.find(t => t.localId === localId);
}
// =========================================================
// API ユーティリティ
// =========================================================
function tempTaskApiHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || '',
    };
}
function getApiBaseUrl() {
    const container = document.getElementById('tempTaskContainer');
    return (container === null || container === void 0 ? void 0 : container.dataset.apiUrl) || '';
}
function getApiClearUrl() {
    const container = document.getElementById('tempTaskContainer');
    return (container === null || container === void 0 ? void 0 : container.dataset.apiClearUrl) || '';
}
async function apiFetch(url, options) {
    return fetch(url, Object.assign(Object.assign({}, options), { headers: tempTaskApiHeaders() }));
}
async function apiGetTasks() {
    const res = await fetch(getApiBaseUrl());
    if (!res.ok)
        throw new Error('タスク取得失敗');
    const data = await res.json();
    return data.tasks;
}
async function apiCreateTask(title, status) {
    const res = await apiFetch(getApiBaseUrl(), {
        method: 'POST',
        body: JSON.stringify({ title, status }),
    });
    if (!res.ok)
        throw new Error('タスク作成失敗');
    return res.json();
}
async function apiUpdateTask(serverId, updates) {
    const res = await apiFetch(`${getApiBaseUrl()}${serverId}/`, {
        method: 'PUT',
        body: JSON.stringify(updates),
    });
    if (!res.ok)
        throw new Error('タスク更新失敗');
    return res.json();
}
async function apiDeleteTask(serverId) {
    const res = await apiFetch(`${getApiBaseUrl()}${serverId}/`, {
        method: 'DELETE',
    });
    if (!res.ok)
        throw new Error('タスク削除失敗');
}
async function apiClearTasks() {
    const res = await apiFetch(getApiClearUrl(), {
        method: 'DELETE',
    });
    if (!res.ok)
        throw new Error('全削除失敗');
}
// =========================================================
// タスク操作（楽観的UI更新 + 非同期保存）
// =========================================================
async function addTask(status) {
    const input = document.getElementById(`input-${status}`);
    if (!input)
        return;
    const title = input.value.trim();
    if (!title) {
        input.focus();
        return;
    }
    // 楽観的UI更新: 即座に未保存状態でリスト追加
    const localId = generateLocalId();
    const newTask = {
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
    // サーバーへ非同期保存
    try {
        const saved = await apiCreateTask(title, status);
        const task = getTaskByLocalId(localId);
        if (task) {
            task.serverId = saved.id;
            task.savedState = 'saved';
            updateCardSavedState(localId);
        }
    }
    catch (_a) {
        const task = getTaskByLocalId(localId);
        if (task) {
            task.savedState = 'error';
            updateCardSavedState(localId);
        }
    }
}
async function deleteTask(localId) {
    const task = getTaskByLocalId(localId);
    if (!task)
        return;
    const serverId = task.serverId;
    tasks = tasks.filter(t => t.localId !== localId);
    renderAll();
    // サーバーへ非同期削除（サーバーIDがある場合のみ）
    if (serverId !== null) {
        try {
            await apiDeleteTask(serverId);
        }
        catch (_a) {
            // 削除失敗は無視（UIからは消えている）
        }
    }
}
async function updateTask(localId, newTitle) {
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
        }
        catch (_a) {
            const t = getTaskByLocalId(localId);
            if (t) {
                t.savedState = 'error';
                updateCardSavedState(localId);
            }
        }
    }
}
async function moveTask(localId, newStatus) {
    const task = getTaskByLocalId(localId);
    if (!task || task.status === newStatus)
        return;
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
        }
        catch (_a) {
            const t = getTaskByLocalId(localId);
            if (t) {
                t.savedState = 'error';
                updateCardSavedState(localId);
            }
        }
    }
}
async function clearAllTasks() {
    if (!confirm('すべてのタスクを削除してもよろしいですか？'))
        return;
    const hasServerTasks = tasks.some(t => t.serverId !== null);
    tasks = [];
    renderAll();
    if (hasServerTasks) {
        try {
            await apiClearTasks();
        }
        catch (_a) {
            // 失敗は無視
        }
    }
}
// =========================================================
// 初期ロード（サーバーからデータ取得）
// =========================================================
async function loadFromServer() {
    try {
        const serverTasks = await apiGetTasks();
        tasks = serverTasks.map(st => ({
            localId: generateLocalId(),
            serverId: st.id,
            title: st.title,
            status: st.status,
            order: st.order,
            savedState: 'saved',
        }));
        renderAll();
    }
    catch (_a) {
        // サーバー取得失敗時は空の状態を表示
        tasks = [];
        renderAll();
    }
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
    const columnTasks = tasks.filter(t => t.status === status);
    container.innerHTML = '';
    columnTasks.forEach(task => container.appendChild(createTaskCard(task)));
    if (countEl)
        countEl.textContent = String(columnTasks.length);
}
function renderAll() {
    renderColumn('todo');
    renderColumn('doing');
    renderColumn('done');
}
function updateCardSavedState(localId) {
    const card = document.querySelector(`[data-local-id="${CSS.escape(localId)}"]`);
    const task = getTaskByLocalId(localId);
    if (!card || !task)
        return;
    card.classList.remove('saving', 'save-error');
    if (task.savedState === 'saving') {
        card.classList.add('saving');
    }
    else if (task.savedState === 'error') {
        card.classList.add('save-error');
    }
}
function createTaskCard(task) {
    var _a;
    const card = document.createElement('div');
    card.className = 'kanban-task-card';
    if (task.savedState === 'saving')
        card.classList.add('saving');
    if (task.savedState === 'error')
        card.classList.add('save-error');
    card.dataset.localId = task.localId;
    card.draggable = true;
    const unsavedIndicator = task.savedState !== 'saved'
        ? `<span class="kanban-task-unsaved-dot" title="${task.savedState === 'error' ? '保存失敗' : '保存中...'}"></span>`
        : '';
    card.innerHTML = `
        <span class="kanban-task-text">${escapeHtml(task.title)}</span>
        ${unsavedIndicator}
        <button class="kanban-task-delete" title="削除" data-local-id="${task.localId}">
            <i class="fas fa-times"></i>
        </button>
    `;
    // 削除ボタン
    (_a = card.querySelector('.kanban-task-delete')) === null || _a === void 0 ? void 0 : _a.addEventListener('click', (e) => {
        e.stopPropagation();
        void deleteTask(task.localId);
    });
    // ダブルクリックで編集（PC）
    card.addEventListener('dblclick', (e) => {
        if (e.target.closest('.kanban-task-delete'))
            return;
        startEdit(task, card);
    });
    // PC: HTML5 Drag & Drop
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    // モバイル: タッチイベント
    card.addEventListener('touchstart', handleTouchStart, { passive: false });
    card.addEventListener('touchmove', handleTouchMove, { passive: false });
    card.addEventListener('touchend', (e) => {
        handleTouchEnd(e, task, card);
    }, { passive: false });
    return card;
}
// =========================================================
// インライン編集
// =========================================================
function startEdit(task, card) {
    const textEl = card.querySelector('.kanban-task-text');
    if (!textEl)
        return;
    card.draggable = false;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = task.title;
    input.className = 'kanban-task-edit-input';
    let committed = false;
    function commit() {
        if (committed)
            return;
        committed = true;
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== task.title) {
            void updateTask(task.localId, newTitle);
        }
        else {
            renderAll();
        }
    }
    function cancel() {
        if (committed)
            return;
        committed = true;
        renderAll();
    }
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
    textEl.replaceWith(input);
    input.focus();
    input.select();
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
    if (overlay) {
        overlay.classList.remove('active');
        overlay.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-zone-hover'));
    }
}
function executeDragAction(action, localId) {
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
function initializeDragOverlay() {
    const overlay = document.getElementById('dragOverlay');
    if (!overlay)
        return;
    overlay.querySelectorAll('.drag-zone').forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (e.dataTransfer)
                e.dataTransfer.dropEffect = 'move';
            overlay.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-zone-hover'));
            zone.classList.add('drag-zone-hover');
        });
        zone.addEventListener('dragleave', (e) => {
            if (zone.contains(e.relatedTarget))
                return;
            zone.classList.remove('drag-zone-hover');
        });
        zone.addEventListener('drop', (e) => {
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
// PC ドラッグ & ドロップ
// =========================================================
function handleDragStart(e) {
    dragSourceEl = e.currentTarget;
    draggedLocalId = dragSourceEl.dataset.localId || null;
    dragSourceEl.classList.add('dragging');
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedLocalId || '');
    }
    requestAnimationFrame(showDragOverlay);
}
function handleDragEnd(_e) {
    if (dragSourceEl)
        dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedLocalId = null;
    hideDragOverlay();
}
// =========================================================
// モバイル タッチドラッグ
// =========================================================
function handleTouchStart(e) {
    if (e.target.closest('.kanban-task-delete'))
        return;
    const t = e.touches[0];
    const card = e.currentTarget;
    touch.localId = card.dataset.localId || null;
    touch.startX = t.clientX;
    touch.startY = t.clientY;
    touch.sourceEl = card;
    touch.isDragging = false;
    touch.cloneEl = null;
    e.preventDefault();
}
function handleTouchMove(e) {
    if (!touch.localId || !touch.sourceEl)
        return;
    const t = e.touches[0];
    const dx = t.clientX - touch.startX;
    const dy = t.clientY - touch.startY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (!touch.isDragging) {
        if (dist < DRAG_THRESHOLD)
            return;
        touch.isDragging = true;
        const card = touch.sourceEl;
        const rect = card.getBoundingClientRect();
        const clone = card.cloneNode(true);
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
    if (!touch.cloneEl || !touch.sourceEl)
        return;
    const rect = touch.sourceEl.getBoundingClientRect();
    touch.cloneEl.style.left = (rect.left + (t.clientX - touch.startX)) + 'px';
    touch.cloneEl.style.top = (rect.top + (t.clientY - touch.startY)) + 'px';
    const overlay = document.getElementById('dragOverlay');
    if (overlay && overlay.classList.contains('active')) {
        overlay.querySelectorAll('.drag-zone').forEach(z => z.classList.remove('drag-zone-hover'));
        touch.cloneEl.style.display = 'none';
        const elBelow = document.elementFromPoint(t.clientX, t.clientY);
        touch.cloneEl.style.display = '';
        const zone = elBelow && elBelow.closest('.drag-zone');
        if (zone)
            zone.classList.add('drag-zone-hover');
    }
}
function handleTouchEnd(e, task, card) {
    if (!touch.localId)
        return;
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
        const zone = elBelow && elBelow.closest('.drag-zone');
        if (zone && touch.localId) {
            executeDragAction(zone.dataset.action || '', touch.localId);
        }
        else {
            renderAll();
        }
        hideDragOverlay();
        touch.localId = null;
        touch.isDragging = false;
    }
    else {
        // ダブルタップ検出
        const now = Date.now();
        if (now - lastTapTime < 300 && lastTapLocalId === task.localId) {
            startEdit(task, card);
            lastTapTime = 0;
            lastTapLocalId = null;
        }
        else {
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
function handleInputKeypress(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const input = e.currentTarget;
        void addTask(input.dataset.status || '');
    }
}
// =========================================================
// リトライ
// =========================================================
const RETRY_INTERVAL_MS = 30000; // 30秒ごと
async function retryFailedTasks() {
    const failedTasks = tasks.filter(t => t.savedState === 'error');
    if (failedTasks.length === 0)
        return;
    for (const task of failedTasks) {
        // 既にローカル状態から消えていたらスキップ
        if (!getTaskByLocalId(task.localId))
            continue;
        task.savedState = 'saving';
        updateCardSavedState(task.localId);
        try {
            if (task.serverId === null) {
                // 作成失敗のリトライ
                const saved = await apiCreateTask(task.title, task.status);
                const t = getTaskByLocalId(task.localId);
                if (t) {
                    t.serverId = saved.id;
                    t.savedState = 'saved';
                    updateCardSavedState(t.localId);
                }
            }
            else {
                // 更新失敗のリトライ（現在の title/status を再送）
                await apiUpdateTask(task.serverId, { title: task.title, status: task.status });
                const t = getTaskByLocalId(task.localId);
                if (t) {
                    t.savedState = 'saved';
                    updateCardSavedState(t.localId);
                }
            }
        }
        catch (_a) {
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
function initializeInputs() {
    document.querySelectorAll('.kanban-input').forEach(el => {
        el.addEventListener('keypress', (e) => handleInputKeypress(e));
    });
}
document.addEventListener('DOMContentLoaded', () => {
    initializeDragOverlay();
    initializeInputs();
    void loadFromServer();
    // 定期リトライ（30秒ごと）
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
