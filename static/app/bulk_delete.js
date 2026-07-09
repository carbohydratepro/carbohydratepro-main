"use strict";
// 選択モード＋一括削除（一覧画面共通）
// テンプレート側の約束:
//   - 一覧全体を [data-bulk-container][data-bulk-url="<一括削除URL>"] で囲む
//   - 「選択」トグルを [data-bulk-toggle] としてコンテナ内に置く
//   - 各削除対象行に class="bulk-item" data-bulk-id="<id>" と
//     <input type="checkbox" class="bulk-check"> を持たせる
// 削除は Undo トーストで数秒間取り消せる（onCommit で keepalive 送信）。
(() => {
    function getCsrf() {
        var _a;
        return (_a = getCookie('csrftoken')) !== null && _a !== void 0 ? _a : '';
    }
    function initBulkContainer(container) {
        const url = container.dataset['bulkUrl'];
        const toggle = container.querySelector('[data-bulk-toggle]');
        if (!url || !toggle)
            return;
        const selected = new Set();
        // 下部アクションバーを生成
        const bar = document.createElement('div');
        bar.className = 'bulk-action-bar';
        bar.innerHTML = `
            <span class="bulk-action-count" aria-live="polite">0件を選択中</span>
            <div class="bulk-action-buttons">
                <button type="button" class="btn btn-sm btn-light bulk-action-cancel">キャンセル</button>
                <button type="button" class="btn btn-sm btn-danger bulk-action-delete" disabled>削除</button>
            </div>
        `;
        document.body.appendChild(bar);
        const countEl = bar.querySelector('.bulk-action-count');
        const deleteBtn = bar.querySelector('.bulk-action-delete');
        const cancelBtn = bar.querySelector('.bulk-action-cancel');
        const items = () => Array.from(container.querySelectorAll('.bulk-item'));
        function updateBar() {
            if (countEl)
                countEl.textContent = `${selected.size}件を選択中`;
            if (deleteBtn)
                deleteBtn.disabled = selected.size === 0;
        }
        function setChecked(item, checked) {
            const id = item.dataset['bulkId'];
            if (!id)
                return;
            const box = item.querySelector('.bulk-check');
            if (box)
                box.checked = checked;
            item.classList.toggle('bulk-selected', checked);
            if (checked)
                selected.add(id);
            else
                selected.delete(id);
            updateBar();
        }
        function enterMode() {
            container.classList.add('bulk-mode');
            document.body.classList.add('bulk-mode-active');
            bar.classList.add('show');
            toggle === null || toggle === void 0 ? void 0 : toggle.setAttribute('aria-pressed', 'true');
        }
        function exitMode() {
            container.classList.remove('bulk-mode');
            document.body.classList.remove('bulk-mode-active');
            bar.classList.remove('show');
            toggle === null || toggle === void 0 ? void 0 : toggle.setAttribute('aria-pressed', 'false');
            items().forEach(item => setChecked(item, false));
            selected.clear();
            updateBar();
        }
        toggle.addEventListener('click', () => {
            if (container.classList.contains('bulk-mode'))
                exitMode();
            else
                enterMode();
        });
        cancelBtn === null || cancelBtn === void 0 ? void 0 : cancelBtn.addEventListener('click', exitMode);
        // 選択モード中は行クリックで選択をトグル（既存の編集・削除操作は抑止）
        container.addEventListener('click', (e) => {
            if (!container.classList.contains('bulk-mode'))
                return;
            const target = e.target;
            const item = target.closest('.bulk-item');
            if (!item || !container.contains(item))
                return;
            // リンクは通常どおり動かす
            if (target.closest('a'))
                return;
            e.preventDefault();
            e.stopPropagation();
            const id = item.dataset['bulkId'];
            if (id)
                setChecked(item, !selected.has(id));
        }, true);
        deleteBtn === null || deleteBtn === void 0 ? void 0 : deleteBtn.addEventListener('click', () => {
            if (selected.size === 0)
                return;
            // デモモードでは実削除せず、デモのインターセプターにブロックさせる
            if (window.DEMO_MODE) {
                void fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                    body: JSON.stringify({ ids: Array.from(selected) }),
                });
                exitMode();
                return;
            }
            const ids = Array.from(selected);
            const targetItems = items().filter(item => {
                const id = item.dataset['bulkId'];
                return id !== undefined && selected.has(id);
            });
            // UIから即座に隠し、本削除はトーストのタイムアウトまで保留する
            targetItems.forEach(item => item.classList.add('bulk-hidden'));
            exitMode();
            showUndoToast({
                message: `${ids.length}件を削除しました`,
                onUndo: () => {
                    targetItems.forEach(item => item.classList.remove('bulk-hidden'));
                },
                onCommit: () => {
                    void fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrf(),
                        },
                        body: JSON.stringify({ ids }),
                        keepalive: true,
                    }).then(res => {
                        if (!res.ok) {
                            // 失敗したら行を戻し、通知する
                            targetItems.forEach(item => item.classList.remove('bulk-hidden'));
                            showToast('削除に失敗しました', 'error');
                        }
                    }).catch(() => {
                        targetItems.forEach(item => item.classList.remove('bulk-hidden'));
                        showToast('削除に失敗しました', 'error');
                    });
                },
            });
        });
        updateBar();
    }
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-bulk-container]').forEach(initBulkContainer);
    });
})();
