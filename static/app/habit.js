"use strict";
// 習慣トラッカー - スワイプ / タブ / ヒートマップ / 年選択 / 日付ナビ
const MONTHS_JA = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
// ---- ヒートマップ ----
function getScoreClass(score) {
    if (score === undefined)
        return ''; // 記録なし → grey (デフォルト)
    if (score === 0)
        return 'score-zero'; // 記録あり score=0 → 薄い黄色
    if (score > 0) {
        if (score < 1)
            return 'score-p1';
        if (score < 2)
            return 'score-p2';
        if (score < 4)
            return 'score-p3';
        return 'score-p4';
    }
    if (score > -1)
        return 'score-n1';
    if (score > -2)
        return 'score-n2';
    if (score > -4)
        return 'score-n3';
    return 'score-n4';
}
function formatDateLabel(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const weekDays = ['日', '月', '火', '水', '木', '金', '土'];
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}(${weekDays[d.getDay()]})`;
}
/**
 * ヒートマップを描画する。
 * year が指定された場合はその年全体（Jan〜Dec）を表示し月ラベルを付ける。
 * year が null の場合は直近365日表示。
 */
function renderHeatmap(data, todayStr, year) {
    const container = document.getElementById('habitHeatmap');
    const monthLabelContainer = document.getElementById('heatmapMonthLabels');
    if (!container)
        return;
    container.innerHTML = '';
    if (monthLabelContainer)
        monthLabelContainer.innerHTML = '';
    const today = new Date(todayStr + 'T00:00:00');
    let startDate;
    let endDate;
    if (year !== null) {
        // 指定年: Jan 1 の直前の月曜日から Dec 31 まで
        const jan1 = new Date(year, 0, 1);
        const dow = jan1.getDay();
        const offset = dow === 0 ? -6 : 1 - dow;
        startDate = new Date(jan1);
        startDate.setDate(jan1.getDate() + offset);
        endDate = new Date(year, 11, 31);
        if (endDate > today)
            endDate = today;
    }
    else {
        // 直近365日: 364日前の月曜日から今日まで
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 364);
        const dow = startDate.getDay();
        const offset = dow === 0 ? -6 : 1 - dow;
        startDate.setDate(startDate.getDate() + offset);
        endDate = today;
    }
    const fragment = document.createDocumentFragment();
    const monthLabelFragment = document.createDocumentFragment();
    const current = new Date(startDate);
    let colIndex = 0;
    // month label positions: { col, label }
    const monthLabels = [];
    let prevMonth = -1;
    while (current <= endDate) {
        const weekDiv = document.createElement('div');
        weekDiv.className = 'heatmap-week';
        for (let d = 0; d < 7; d++) {
            const cellDate = new Date(current);
            cellDate.setDate(current.getDate() + d);
            // 月ラベルの位置を記録（週の最初の日で判定）
            if (d === 0) {
                const m = cellDate.getMonth();
                if (m !== prevMonth && cellDate <= endDate) {
                    // 年指定モードでは対象年のセルのみラベルを記録（前年12月分をスキップ）
                    if (year === null || cellDate.getFullYear() === year) {
                        const label = (year !== null && m === 0)
                            ? `${String(year)}/${MONTHS_JA[m]}`
                            : MONTHS_JA[m];
                        monthLabels.push({ col: colIndex, label });
                    }
                    prevMonth = m;
                }
            }
            const isFuture = cellDate > endDate;
            const isOutOfYear = year !== null && cellDate.getFullYear() !== year;
            if (isFuture || isOutOfYear) {
                const placeholder = document.createElement('div');
                placeholder.className = 'heatmap-cell future';
                weekDiv.appendChild(placeholder);
                continue;
            }
            const dateStr = cellDate.toISOString().split('T')[0];
            const score = data[dateStr];
            const scoreClass = getScoreClass(score);
            const cell = document.createElement('div');
            cell.className = 'heatmap-cell' + (scoreClass ? ' ' + scoreClass : '');
            if (dateStr === todayStr)
                cell.classList.add('today');
            const scoreVal = score !== null && score !== void 0 ? score : 0;
            // スコアは整数で表示（カンマなし）
            const scoreInt = Math.round(scoreVal);
            const scoreLabel = scoreVal !== 0 ? `\nスコア: ${scoreInt}` : (score !== undefined ? '\nスコア: 0（相殺）' : '');
            cell.title = `${formatDateLabel(dateStr)}${scoreLabel}`;
            cell.dataset['date'] = dateStr;
            cell.dataset['score'] = String(scoreVal);
            cell.dataset['hasRecord'] = score !== undefined ? '1' : '0';
            weekDiv.appendChild(cell);
        }
        fragment.appendChild(weekDiv);
        current.setDate(current.getDate() + 7);
        colIndex++;
    }
    container.appendChild(fragment);
    // 月ラベル描画
    if (monthLabelContainer && monthLabels.length > 0) {
        for (let i = 0; i < monthLabels.length; i++) {
            const { col, label } = monthLabels[i];
            const nextCol = i + 1 < monthLabels.length ? monthLabels[i + 1].col : colIndex;
            const width = (nextCol - col) * (13 + 3); // cell(13) + gap(3)
            const span = document.createElement('div');
            span.className = 'heatmap-month-label';
            span.textContent = label;
            span.style.width = `${width}px`;
            monthLabelFragment.appendChild(span);
        }
        monthLabelContainer.appendChild(monthLabelFragment);
    }
}
function updateHeatmapCell(dateStr, newScore, hasRecord) {
    const cell = document.querySelector(`.heatmap-cell[data-date="${dateStr}"]`);
    if (!cell)
        return;
    cell.dataset['score'] = String(newScore);
    cell.className = 'heatmap-cell';
    if (dateStr === habitToday)
        cell.classList.add('today');
    const scoreData = hasRecord ? newScore : undefined;
    const cls = getScoreClass(scoreData);
    if (cls)
        cell.classList.add(cls);
    const scoreInt = Math.round(newScore);
    const scoreLabel = newScore !== 0 ? `\nスコア: ${scoreInt}` : (hasRecord ? '\nスコア: 0（相殺）' : '');
    cell.title = `${formatDateLabel(dateStr)}${scoreLabel}`;
}
/** トグル後にヒートマップセルをスコア差分で更新する */
function applyHeatmapDelta(dateStr, scoreDelta, nowCompleted) {
    var _a;
    const cell = document.querySelector(`.heatmap-cell[data-date="${dateStr}"]`);
    if (!cell)
        return;
    const prevScore = parseFloat((_a = cell.dataset['score']) !== null && _a !== void 0 ? _a : '0');
    const newScore = prevScore + scoreDelta;
    // レコードがあるかどうか: 今回達成 or 既存レコードがある
    const prevHasRecord = cell.dataset['hasRecord'] === '1';
    const hasRecord = nowCompleted || prevHasRecord;
    if (nowCompleted)
        cell.dataset['hasRecord'] = '1';
    updateHeatmapCell(dateStr, newScore, hasRecord);
}
/** 週ビューのセル（ドット）と達成数バッジをトグル後に更新する */
function updateWeekCell(habitId, dateStr, completed, color) {
    var _a, _b;
    const row = document.querySelector(`tr[data-habit-id="${habitId}"]`);
    if (!row)
        return;
    const headers = Array.from(document.querySelectorAll('th[data-week-date]'));
    const colIndex = headers.findIndex(h => h.dataset['weekDate'] === dateStr);
    if (colIndex < 0)
        return;
    // セル: +1 は習慣名列の分
    const cells = row.querySelectorAll('td');
    const cell = cells[colIndex + 1];
    if (!cell)
        return;
    const dot = cell.querySelector('.week-dot');
    if (!dot)
        return;
    if (completed) {
        dot.classList.add('done');
        dot.style.background = color;
        dot.style.border = 'none';
    }
    else {
        dot.classList.remove('done');
        dot.style.background = '';
        dot.style.border = '';
    }
    // 達成数バッジを更新
    const allDots = Array.from(row.querySelectorAll('.week-dot'));
    const doneCount = allDots.filter(d => d.classList.contains('done')).length;
    const badge = row.querySelector('.week-goal-badge');
    if (badge) {
        const currentText = (_b = (_a = badge.textContent) === null || _a === void 0 ? void 0 : _a.trim()) !== null && _b !== void 0 ? _b : '';
        const slash = currentText.indexOf('/');
        if (slash >= 0) {
            const goal = currentText.slice(slash + 1);
            badge.textContent = `${doneCount}/${goal}`;
            const goalNum = parseInt(goal, 10);
            badge.className = `week-goal-badge badge ${goalNum > 0 && doneCount >= goalNum ? 'badge-success' : 'badge-secondary'}`;
        }
        else {
            badge.textContent = String(doneCount);
        }
    }
}
// ---- AJAX トグル ----
async function doToggle(habitId, dateStr, coefficient) {
    var _a, _b, _c;
    const tokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = (_a = tokenEl === null || tokenEl === void 0 ? void 0 : tokenEl.value) !== null && _a !== void 0 ? _a : '';
    const resp = await fetch('/carbohydratepro/habits/toggle/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
        body: `habit_id=${habitId}&date=${dateStr}&coefficient=${coefficient}`,
    });
    const data = await resp.json();
    if (data.error) {
        console.error('toggle error:', data.error);
        return null;
    }
    return { completed: (_b = data.completed) !== null && _b !== void 0 ? _b : false, score_delta: (_c = data.score_delta) !== null && _c !== void 0 ? _c : 0 };
}
function moveCard(card, toCompleted) {
    var _a, _b;
    const undoneList = document.getElementById('undoneList');
    const doneList = document.getElementById('doneList');
    if (!undoneList || !doneList)
        return;
    card.dataset['completed'] = toCompleted ? '1' : '0';
    if (toCompleted) {
        card.classList.add('done');
        if (!card.querySelector('.done-icon')) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-check done-icon';
            (_a = card.querySelector('.habit-card-main')) === null || _a === void 0 ? void 0 : _a.appendChild(icon);
        }
        doneList.appendChild(card);
    }
    else {
        card.classList.remove('done');
        (_b = card.querySelector('.done-icon')) === null || _b === void 0 ? void 0 : _b.remove();
        undoneList.appendChild(card);
    }
}
// ---- カードスワイプ ----
const SWIPE_THRESHOLD = 60;
// カードが横スワイプ中かどうかを示すフラグ（パネル切替の誤作動防止）
let isCardDragging = false;
function getCardCoefficient(card) {
    const slider = card.querySelector('.coeff-slider');
    return slider ? slider.value : '1';
}
/** スライダー操作中かどうかを判定 */
function isSliderInteraction(target) {
    if (!target)
        return false;
    const el = target;
    return el.classList.contains('coeff-slider') || el.closest('.coeff-slider-wrap') !== null;
}
function attachCardSwipe(card) {
    let startX = 0;
    let startY = 0;
    let isDragging = false;
    let isVertical = false; // 縦スクロール中フラグ
    let directionLocked = false; // 方向確定フラグ
    const leftHint = card.querySelector('.habit-card-swipe-hint.left');
    const rightHint = card.querySelector('.habit-card-swipe-hint.right');
    function onStart(x, y, target) {
        // スライダー操作中はスワイプ無効
        if (isSliderInteraction(target))
            return false;
        startX = x;
        startY = y;
        isDragging = false;
        isVertical = false;
        directionLocked = false;
        return true;
    }
    function onMove(x, y) {
        const dx = x - startX;
        const dy = y - startY;
        const absDx = Math.abs(dx);
        const absDy = Math.abs(dy);
        // 方向未確定 かつ 十分な移動量がある場合に方向を確定
        if (!directionLocked && (absDx > 8 || absDy > 8)) {
            directionLocked = true;
            isVertical = absDy >= absDx;
        }
        // 縦スクロール中はカード移動しない
        if (isVertical)
            return;
        // 完了状態に応じてスライド方向を制限（完了済み→左のみ、未完了→右のみ）
        const completed = card.dataset['completed'] === '1';
        if (completed && dx > 0)
            return;
        if (!completed && dx < 0)
            return;
        if (!isDragging && absDx > 8) {
            isDragging = true;
            isCardDragging = true; // パネル切替の誤作動防止
        }
        if (!isDragging)
            return;
        card.style.transform = `translateX(${dx}px)`;
        const ratio = Math.min(absDx / SWIPE_THRESHOLD, 1);
        if (leftHint)
            leftHint.style.opacity = dx < 0 ? String(ratio) : '0';
        if (rightHint)
            rightHint.style.opacity = dx > 0 ? String(ratio) : '0';
    }
    async function onEnd(x) {
        var _a, _b, _c, _d, _e, _f, _g;
        const dx = x - startX;
        card.style.transform = '';
        if (leftHint)
            leftHint.style.opacity = '0';
        if (rightHint)
            rightHint.style.opacity = '0';
        if (!isDragging || isVertical)
            return;
        isDragging = false;
        const completed = card.dataset['completed'] === '1';
        const shouldComplete = dx > SWIPE_THRESHOLD;
        const shouldUncomplete = dx < -SWIPE_THRESHOLD;
        const coeff = getCardCoefficient(card);
        const dateStr = (_a = card.dataset['date']) !== null && _a !== void 0 ? _a : habitSelectedDate;
        if (shouldComplete && !completed) {
            const res = await doToggle((_b = card.dataset['habitId']) !== null && _b !== void 0 ? _b : '', dateStr, coeff);
            if (res) {
                moveCard(card, true);
                applyHeatmapDelta(dateStr, res.score_delta, true);
                updateWeekCell((_c = card.dataset['habitId']) !== null && _c !== void 0 ? _c : '', dateStr, true, (_d = card.dataset['color']) !== null && _d !== void 0 ? _d : '');
            }
        }
        else if (shouldUncomplete && completed) {
            const res = await doToggle((_e = card.dataset['habitId']) !== null && _e !== void 0 ? _e : '', dateStr, coeff);
            if (res) {
                moveCard(card, false);
                applyHeatmapDelta(dateStr, res.score_delta, false);
                updateWeekCell((_f = card.dataset['habitId']) !== null && _f !== void 0 ? _f : '', dateStr, false, (_g = card.dataset['color']) !== null && _g !== void 0 ? _g : '');
            }
        }
    }
    card.addEventListener('touchstart', (e) => {
        onStart(e.touches[0].clientX, e.touches[0].clientY, e.target);
    }, { passive: true });
    card.addEventListener('touchmove', (e) => {
        onMove(e.touches[0].clientX, e.touches[0].clientY);
        if (isDragging && !isVertical)
            e.preventDefault();
    }, { passive: false });
    card.addEventListener('touchend', (e) => onEnd(e.changedTouches[0].clientX));
    card.addEventListener('mousedown', (e) => {
        if (!onStart(e.clientX, e.clientY, e.target))
            return;
        const onUp = (ev) => {
            onEnd(ev.clientX);
            document.removeEventListener('mouseup', onUp);
            document.removeEventListener('mousemove', onMv);
        };
        const onMv = (ev) => onMove(ev.clientX, ev.clientY);
        document.addEventListener('mousemove', onMv);
        document.addEventListener('mouseup', onUp);
    });
}
// ---- 係数スライダー（カード内） ----
function attachCardSlider(card) {
    const slider = card.querySelector('.coeff-slider');
    const label = card.querySelector('.coeff-val');
    if (!slider || !label)
        return;
    const isPositive = slider.dataset['positive'] !== 'false';
    slider.addEventListener('input', () => {
        label.textContent = `${isPositive ? '+' : '-'}${slider.value}`;
    });
}
// ---- タブ & パネルスワイプ ----
let currentPanel = 0;
const PANEL_COUNT = 3;
function updateWrapHeight() {
    const wrap = document.getElementById('habitPanelsWrap');
    const panels = document.querySelectorAll('.habit-panel');
    if (!wrap || panels.length === 0)
        return;
    const panel = panels[currentPanel];
    if (panel)
        wrap.style.height = `${panel.scrollHeight}px`;
}
function switchPanel(index) {
    if (index < 0 || index >= PANEL_COUNT)
        return;
    currentPanel = index;
    const panels = document.getElementById('habitPanels');
    if (panels)
        panels.style.transform = `translateX(-${index * 100}%)`;
    document.querySelectorAll('.habit-tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
    });
    // パネル切り替え後に高さを更新
    setTimeout(updateWrapHeight, 50);
}
function attachPanelSwipe() {
    const wrap = document.getElementById('habitPanelsWrap');
    if (!wrap)
        return;
    let startX = 0;
    let startY = 0;
    let dragging = false;
    wrap.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        dragging = false;
        isCardDragging = false; // 新しいタッチ開始時にフラグをリセット
    }, { passive: true });
    wrap.addEventListener('touchmove', (e) => {
        const dx = e.touches[0].clientX - startX;
        const dy = e.touches[0].clientY - startY;
        if (!dragging && Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy))
            dragging = true;
    }, { passive: true });
    wrap.addEventListener('touchend', (e) => {
        // カードスワイプ中はパネル切替しない
        if (!dragging || isCardDragging)
            return;
        const dx = e.changedTouches[0].clientX - startX;
        if (dx < -50)
            switchPanel(currentPanel + 1);
        else if (dx > 50)
            switchPanel(currentPanel - 1);
    });
}
// ---- 日付ナビ（date picker） ----
async function loadDateStatus(dateStr) {
    try {
        const resp = await fetch(`/carbohydratepro/habits/status/?date=${dateStr}`);
        if (!resp.ok) {
            console.error('status fetch error:', resp.status);
            return;
        }
        const json = await resp.json();
        const undoneList = document.getElementById('undoneList');
        const doneList = document.getElementById('doneList');
        if (!undoneList || !doneList)
            return;
        undoneList.innerHTML = '';
        doneList.innerHTML = '';
        for (const item of json.status) {
            const card = buildCard(item, dateStr);
            attachCardSwipe(card);
            attachCardSlider(card);
            if (item['completed'])
                doneList.appendChild(card);
            else
                undoneList.appendChild(card);
        }
        // date picker の値を更新
        const picker = document.getElementById('datePickerInput');
        if (picker)
            picker.value = dateStr;
        // パネル高さ更新
        updateWrapHeight();
    }
    catch (err) {
        console.error('loadDateStatus error:', err);
    }
}
function buildCard(item, dateStr) {
    const completed = item['completed'];
    const isPositive = item['is_positive'];
    const defaultCoeff = item['default_coefficient'];
    const usedCoeff = item['used_coefficient'];
    const color = item['color'];
    const signChar = isPositive ? '+' : '-';
    const displayCoeff = completed ? usedCoeff : defaultCoeff;
    const card = document.createElement('div');
    card.className = `habit-card${completed ? ' done' : ''}`;
    card.dataset['habitId'] = String(item['id']);
    card.dataset['date'] = dateStr;
    card.dataset['completed'] = completed ? '1' : '0';
    card.dataset['color'] = color;
    card.dataset['defaultCoeff'] = String(defaultCoeff);
    card.dataset['score'] = '0';
    card.innerHTML = `
    <div class="habit-card-swipe-hint left"><i class="fas fa-times"></i></div>
    <div class="habit-card-swipe-hint right"><i class="fas fa-check"></i></div>
    <div class="habit-card-main">
      <div class="habit-card-indicator" style="background:${color};"></div>
      <div class="habit-card-body">
        <div class="habit-card-title">${String(item['title'])}</div>
        <div class="habit-card-meta">${String(item['frequency'])}</div>
      </div>
      ${completed ? '<i class="fas fa-check done-icon"></i>' : ''}
    </div>
    <div class="coeff-slider-wrap">
      <span class="coeff-slider-label">係数: <span class="coeff-val">${signChar}${displayCoeff}</span></span>
      <input type="range" class="coeff-slider" min="1" max="10" step="1" value="${displayCoeff}" data-positive="${isPositive}">
    </div>
  `;
    return card;
}
// ---- 年ビュー ----
async function loadYearHeatmap(year) {
    try {
        const url = year !== null
            ? `/carbohydratepro/habits/heatmap/?year=${year}`
            : '/carbohydratepro/habits/heatmap/';
        const resp = await fetch(url);
        if (!resp.ok) {
            console.error('heatmap fetch error:', resp.status);
            return;
        }
        const data = await resp.json();
        renderHeatmap(data, habitToday, year);
        // 年ビューのパネル高さ更新
        setTimeout(updateWrapHeight, 50);
    }
    catch (err) {
        console.error('loadYearHeatmap error:', err);
    }
}
// ---- 日付詳細表示（週/年ビューのクリック） ----
async function showDayDetail(dateStr) {
    const section = document.getElementById('dayDetailSection');
    const content = document.getElementById('dayDetailContent');
    const titleEl = document.getElementById('dayDetailDate');
    if (!section || !content)
        return;
    try {
        const resp = await fetch(`/carbohydratepro/habits/status/?date=${dateStr}`);
        if (!resp.ok)
            return;
        const json = await resp.json();
        if (json.error)
            return;
        if (titleEl)
            titleEl.textContent = formatDateLabel(dateStr);
        content.innerHTML = '';
        if (json.status.length === 0) {
            content.innerHTML = '<p class="text-muted small mb-0">習慣が登録されていません。</p>';
        }
        else {
            for (const item of json.status) {
                const completed = item['completed'];
                const color = item['color'];
                const row = document.createElement('div');
                row.className = 'day-detail-row';
                row.innerHTML = `
          <span class="day-detail-dot" style="background:${color};"></span>
          <span class="day-detail-title">${String(item['title'])}</span>
          <span class="day-detail-status ${completed ? 'done' : 'undone'}">
            <i class="fas ${completed ? 'fa-check' : 'fa-times'}"></i>
          </span>
        `;
                content.appendChild(row);
            }
        }
        section.style.display = 'block';
        section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    catch (err) {
        console.error('showDayDetail error:', err);
    }
}
function closeDayDetail() {
    const section = document.getElementById('dayDetailSection');
    if (section)
        section.style.display = 'none';
}
// ---- モーダル（追加/編集） ----
function habitSelectPositive(prefix, positive) {
    const posBtn = document.getElementById(`${prefix}PositiveBtn`);
    const negBtn = document.getElementById(`${prefix}NegativeBtn`);
    const input = document.getElementById(`${prefix}IsPositive`);
    if (posBtn)
        posBtn.classList.toggle('selected', positive);
    if (negBtn)
        negBtn.classList.toggle('selected', !positive);
    if (input)
        input.value = positive ? 'true' : 'false';
}
function habitFreqChanged(prefix) {
    var _a;
    const freq = (_a = document.getElementById(`${prefix}Frequency`)) === null || _a === void 0 ? void 0 : _a.value;
    const weeklyField = document.getElementById(`${prefix}WeeklyGoalField`);
    const monthlyField = document.getElementById(`${prefix}MonthlyGoalField`);
    if (weeklyField)
        weeklyField.classList.toggle('hidden', freq !== 'weekly');
    if (monthlyField)
        monthlyField.classList.toggle('hidden', freq !== 'monthly');
}
function openEditHabit(id, title, frequency, coefficient, isPositive, weeklyGoal, monthlyGoal) {
    const form = document.getElementById('editHabitForm');
    if (!form)
        return;
    form.action = `/carbohydratepro/habits/edit/${id}/`;
    const titleEl = document.getElementById('editTitle');
    const freqEl = document.getElementById('editFrequency');
    const coeffEl = document.getElementById('editCoefficient');
    const coeffValEl = document.getElementById('editCoeffVal');
    const weeklyEl = document.getElementById('editWeeklyGoal');
    const monthlyEl = document.getElementById('editMonthlyGoal');
    if (titleEl)
        titleEl.value = title;
    if (freqEl) {
        freqEl.value = frequency;
        habitFreqChanged('edit');
    }
    if (coeffEl)
        coeffEl.value = String(coefficient);
    if (coeffValEl)
        coeffValEl.textContent = String(coefficient);
    if (weeklyEl)
        weeklyEl.value = String(weeklyGoal);
    if (monthlyEl)
        monthlyEl.value = String(monthlyGoal);
    habitSelectPositive('edit', isPositive);
    // 頻度に応じた目標フィールド表示
    const weeklyField = document.getElementById('editWeeklyGoalField');
    const monthlyField = document.getElementById('editMonthlyGoalField');
    if (weeklyField)
        weeklyField.classList.toggle('hidden', frequency !== 'weekly');
    if (monthlyField)
        monthlyField.classList.toggle('hidden', frequency !== 'monthly');
    $('#editHabitModal').modal('show');
}
function initHabitListInteractions() {
    document.querySelectorAll('.habit-mgmt-item.lp-delete-item').forEach(item => {
        var _a;
        const habitId = parseInt((_a = item.dataset['habitId']) !== null && _a !== void 0 ? _a : '0', 10);
        if (!habitId)
            return;
        let lastTapTime = 0;
        let suppressClick = false;
        let clickCount = 0;
        let clickTimer = null;
        function openEdit() {
            var _a, _b, _c, _d, _e;
            const title = (_a = item.dataset['habitTitle']) !== null && _a !== void 0 ? _a : '';
            const frequency = (_b = item.dataset['habitFrequency']) !== null && _b !== void 0 ? _b : 'daily';
            const coefficient = parseFloat((_c = item.dataset['habitCoefficient']) !== null && _c !== void 0 ? _c : '1');
            const isPositive = item.dataset['habitIsPositive'] === 'true';
            const weeklyGoal = parseInt((_d = item.dataset['habitWeeklyGoal']) !== null && _d !== void 0 ? _d : '0', 10);
            const monthlyGoal = parseInt((_e = item.dataset['habitMonthlyGoal']) !== null && _e !== void 0 ? _e : '0', 10);
            openEditHabit(habitId, title, frequency, coefficient, isPositive, weeklyGoal, monthlyGoal);
        }
        item.addEventListener('touchend', (e) => {
            const target = e.target;
            if (isInteractiveTarget(target) || item.classList.contains('delete-pending'))
                return;
            const now = Date.now();
            if (now - lastTapTime < 400) {
                e.preventDefault();
                suppressClick = true;
                lastTapTime = 0;
                openEdit();
            }
            else {
                lastTapTime = now;
            }
        }, { passive: false });
        item.addEventListener('click', (e) => {
            if (suppressClick) {
                suppressClick = false;
                return;
            }
            const target = e.target;
            if (isInteractiveTarget(target) || item.classList.contains('delete-pending'))
                return;
            clickCount++;
            if (clickCount === 1) {
                clickTimer = setTimeout(() => { clickCount = 0; }, 400);
            }
            else if (clickCount >= 2) {
                if (clickTimer !== null)
                    clearTimeout(clickTimer);
                clickCount = 0;
                openEdit();
            }
        });
    });
}
// ---- 初期化 ----
document.addEventListener('DOMContentLoaded', () => {
    // 習慣一覧ページ（habit list）
    if (document.querySelector('.habit-mgmt-list')) {
        initLongPressDelete();
        initHabitListInteractions();
    }
    // ヒートマップ（ダッシュボードのみ）
    if (!document.getElementById('habitHeatmap'))
        return;
    renderHeatmap(heatmapData, habitToday, habitSelectedYear);
    // 初期高さ設定
    setTimeout(updateWrapHeight, 100);
    // 習慣カード
    document.querySelectorAll('.habit-card').forEach(card => {
        attachCardSwipe(card);
        attachCardSlider(card);
    });
    // タブ
    document.querySelectorAll('.habit-tab').forEach((tab, i) => {
        tab.addEventListener('click', () => switchPanel(i));
    });
    attachPanelSwipe();
    // 日付 picker
    const datePicker = document.getElementById('datePickerInput');
    if (datePicker) {
        datePicker.addEventListener('change', () => {
            const d = datePicker.value;
            if (d)
                loadDateStatus(d);
        });
    }
    // 年ナビ
    document.querySelectorAll('.year-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            var _a;
            const yearStr = (_a = btn.dataset['year']) !== null && _a !== void 0 ? _a : '';
            const year = yearStr ? parseInt(yearStr.replace(/,/g, ''), 10) : null;
            loadYearHeatmap(year);
            document.querySelectorAll('.year-nav-btn').forEach(b => {
                b.classList.toggle('btn-primary', b.dataset['year'] === yearStr);
                b.classList.toggle('btn-outline-secondary', b.dataset['year'] !== yearStr);
            });
        });
    });
    // 週ビュー: 日付ヘッダークリックで詳細表示
    document.querySelectorAll('[data-week-date]').forEach(el => {
        el.addEventListener('click', () => {
            var _a;
            const d = (_a = el.dataset['weekDate']) !== null && _a !== void 0 ? _a : '';
            if (d)
                showDayDetail(d);
        });
    });
    // 年ビュー: ヒートマップセルクリックで詳細表示（イベント委譲）
    const heatmapContainer = document.getElementById('habitHeatmap');
    if (heatmapContainer) {
        heatmapContainer.addEventListener('click', (e) => {
            const cell = e.target.closest('.heatmap-cell[data-date]');
            if (cell && cell.dataset['date'])
                showDayDetail(cell.dataset['date']);
        });
    }
});
