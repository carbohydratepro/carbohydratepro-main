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
// 長押し検出用
let longPressTimerId = null;
let deletePendingLocalId = null;
let deleteModeAutoTimeoutId = null;
const DRAG_THRESHOLD = 8; // px
const LONG_PRESS_DURATION = 500; // ms
const DELETE_MODE_TIMEOUT = 3000; // ms: 操作がなければ自動キャンセル
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
function isDesktopLayout() {
    return window.innerWidth >= 768;
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
    // 未保存ドットを更新
    const dot = card.querySelector('.kanban-task-unsaved-dot');
    if (task.savedState !== 'saved') {
        if (!dot) {
            const newDot = document.createElement('span');
            newDot.className = 'kanban-task-unsaved-dot';
            newDot.title = task.savedState === 'error' ? '保存失敗' : '保存中...';
            const deleteOverlay = card.querySelector('.kanban-task-delete-overlay');
            if (deleteOverlay)
                card.insertBefore(newDot, deleteOverlay);
        }
        else {
            dot.title = task.savedState === 'error' ? '保存失敗' : '保存中...';
        }
    }
    else {
        dot === null || dot === void 0 ? void 0 : dot.remove();
    }
}
function createTaskCard(task) {
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
        <div class="kanban-task-delete-overlay" title="削除">
            <i class="fas fa-trash-alt"></i>
        </div>
    `;
    // 削除オーバーレイ（長押し後に表示）のクリックで削除
    const deleteOverlay = card.querySelector('.kanban-task-delete-overlay');
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
    card.addEventListener('dblclick', (e) => {
        if (e.target.closest('.kanban-task-delete-overlay'))
            return;
        if (deletePendingLocalId === task.localId) {
            deactivateDeleteMode();
            return;
        }
        startEdit(task, card);
    });
    // PC: 長押し検出（mousedown/mouseup/mouseleave）
    card.addEventListener('mousedown', (e) => {
        if (e.button !== 0)
            return;
        if (e.target.closest('.kanban-task-delete-overlay'))
            return;
        if (deletePendingLocalId) {
            deactivateDeleteMode();
            return;
        }
        startLongPressTimer(task.localId);
    });
    card.addEventListener('mouseup', cancelLongPressTimer);
    card.addEventListener('mouseleave', cancelLongPressTimer);
    // PC: HTML5 Drag & Drop
    card.addEventListener('dragstart', (e) => {
        cancelLongPressTimer();
        handleDragStart(e);
    });
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
// 長押し削除モード
// =========================================================
function startLongPressTimer(localId) {
    cancelLongPressTimer();
    longPressTimerId = setTimeout(() => {
        activateDeleteMode(localId);
    }, LONG_PRESS_DURATION);
}
function cancelLongPressTimer() {
    if (longPressTimerId !== null) {
        clearTimeout(longPressTimerId);
        longPressTimerId = null;
    }
}
function activateDeleteMode(localId) {
    deactivateDeleteMode();
    const card = document.querySelector(`[data-local-id="${CSS.escape(localId)}"]`);
    if (!card)
        return;
    deletePendingLocalId = localId;
    card.classList.add('delete-pending');
    card.draggable = false;
    // 軽いバイブレーションフィードバック（対応端末のみ）
    if (navigator.vibrate)
        navigator.vibrate(40);
    // 3秒後に自動キャンセル
    deleteModeAutoTimeoutId = setTimeout(deactivateDeleteMode, DELETE_MODE_TIMEOUT);
    // カード外クリックでキャンセル
    setTimeout(() => {
        document.addEventListener('click', handleOutsideClickForDeleteMode, { once: true });
    }, 0);
}
function deactivateDeleteMode() {
    if (deleteModeAutoTimeoutId !== null) {
        clearTimeout(deleteModeAutoTimeoutId);
        deleteModeAutoTimeoutId = null;
    }
    if (!deletePendingLocalId)
        return;
    const card = document.querySelector(`[data-local-id="${CSS.escape(deletePendingLocalId)}"]`);
    if (card) {
        card.classList.remove('delete-pending');
        card.draggable = true;
    }
    deletePendingLocalId = null;
}
function handleOutsideClickForDeleteMode(e) {
    const target = e.target;
    if (!target.closest('.kanban-task-delete-overlay')) {
        deactivateDeleteMode();
    }
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
// PC ドラッグ & ドロップ（デスクトップ: カラム直接ドロップ）
// =========================================================
function showDeleteZone() {
    const zone = document.getElementById('kanbanDeleteZone');
    if (zone)
        zone.classList.add('active');
}
function hideDeleteZone() {
    const zone = document.getElementById('kanbanDeleteZone');
    if (zone)
        zone.classList.remove('active', 'drag-over');
}
function initializeDeleteZone() {
    const zone = document.getElementById('kanbanDeleteZone');
    if (!zone)
        return;
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (e.dataTransfer)
            e.dataTransfer.dropEffect = 'move';
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', (e) => {
        if (zone.contains(e.relatedTarget))
            return;
        zone.classList.remove('drag-over');
    });
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (draggedLocalId) {
            void deleteTask(draggedLocalId);
        }
        hideDeleteZone();
    });
}
function initializeColumnDropZones() {
    document.querySelectorAll('.kanban-tasks').forEach(col => {
        col.addEventListener('dragover', (e) => {
            if (!isDesktopLayout())
                return;
            e.preventDefault();
            if (e.dataTransfer)
                e.dataTransfer.dropEffect = 'move';
            col.classList.add('drag-over');
        });
        col.addEventListener('dragleave', (e) => {
            if (col.contains(e.relatedTarget))
                return;
            col.classList.remove('drag-over');
        });
        col.addEventListener('drop', (e) => {
            e.preventDefault();
            col.classList.remove('drag-over');
            if (!isDesktopLayout())
                return;
            const status = col.dataset.status || '';
            if (draggedLocalId && status) {
                void moveTask(draggedLocalId, status);
            }
        });
    });
}
function handleDragStart(e) {
    dragSourceEl = e.currentTarget;
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
        else {
            showDragOverlay();
        }
    });
}
function handleDragEnd(_e) {
    if (dragSourceEl)
        dragSourceEl.classList.remove('dragging');
    dragSourceEl = null;
    draggedLocalId = null;
    hideDragOverlay();
    hideDeleteZone();
    document.querySelectorAll('.kanban-tasks').forEach(c => c.classList.remove('drag-over'));
}
// =========================================================
// ドラッグオーバーレイ（モバイル用5ゾーン）
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
// モバイル タッチドラッグ
// =========================================================
function handleTouchStart(e) {
    // 削除オーバーレイのタッチはカードハンドラに流さない
    if (e.target.closest('.kanban-task-delete-overlay'))
        return;
    // 削除モード中は一旦キャンセル
    if (deletePendingLocalId) {
        deactivateDeleteMode();
        return;
    }
    const t = e.touches[0];
    const card = e.currentTarget;
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
        // ドラッグ開始 → 長押しキャンセル
        cancelLongPressTimer();
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
    cancelLongPressTimer();
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
const RETRY_INTERVAL_MS = 30000;
async function retryFailedTasks() {
    const failedTasks = tasks.filter(t => t.savedState === 'error');
    if (failedTasks.length === 0)
        return;
    for (const task of failedTasks) {
        if (!getTaskByLocalId(task.localId))
            continue;
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
            }
            else {
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
    initializeDeleteZone();
    initializeColumnDropZones();
    initializeInputs();
    void loadFromServer();
    // Escape キーで削除モードキャンセル
    document.addEventListener('keydown', (e) => {
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
