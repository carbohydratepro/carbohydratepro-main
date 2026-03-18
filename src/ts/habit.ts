// 習慣トラッカー - スワイプ / タブ / ヒートマップ / 年選択 / 日付ナビ

declare const heatmapData: Record<string, number>;
declare const habitToday: string;
declare const habitSelectedDate: string;
declare const habitSelectedYear: number | null;

const MONTHS_JA = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// ---- ヒートマップ ----

function getScoreClass(score: number | undefined): string {
  if (score === undefined) return '';          // 記録なし → grey (デフォルト)
  if (score === 0) return 'score-zero';        // 記録あり score=0 → 薄い黄色
  if (score > 0) {
    if (score < 1) return 'score-p1';
    if (score < 2) return 'score-p2';
    if (score < 4) return 'score-p3';
    return 'score-p4';
  }
  if (score > -1) return 'score-n1';
  if (score > -2) return 'score-n2';
  if (score > -4) return 'score-n3';
  return 'score-n4';
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  const weekDays = ['日', '月', '火', '水', '木', '金', '土'];
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}(${weekDays[d.getDay()]})`;
}

/**
 * ヒートマップを描画する。
 * year が指定された場合はその年全体（Jan〜Dec）を表示し月ラベルを付ける。
 * year が null の場合は直近365日表示。
 */
function renderHeatmap(data: Record<string, number>, todayStr: string, year: number | null): void {
  const container = document.getElementById('habitHeatmap');
  const monthLabelContainer = document.getElementById('heatmapMonthLabels');
  if (!container) return;
  container.innerHTML = '';
  if (monthLabelContainer) monthLabelContainer.innerHTML = '';

  const today = new Date(todayStr + 'T00:00:00');

  let startDate: Date;
  let endDate: Date;

  if (year !== null) {
    // 指定年: Jan 1 の直前の月曜日から Dec 31 まで
    const jan1 = new Date(year, 0, 1);
    const dow = jan1.getDay();
    const offset = dow === 0 ? -6 : 1 - dow;
    startDate = new Date(jan1);
    startDate.setDate(jan1.getDate() + offset);
    endDate = new Date(year, 11, 31);
    if (endDate > today) endDate = today;
  } else {
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
  const monthLabels: { col: number; label: string }[] = [];
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
      const score: number | undefined = data[dateStr];
      const scoreClass = getScoreClass(score);

      const cell = document.createElement('div');
      cell.className = 'heatmap-cell' + (scoreClass ? ' ' + scoreClass : '');
      if (dateStr === todayStr) cell.classList.add('today');

      const scoreVal = score ?? 0;
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

function updateHeatmapCell(dateStr: string, newScore: number, hasRecord: boolean): void {
  const cell = document.querySelector<HTMLElement>(`.heatmap-cell[data-date="${dateStr}"]`);
  if (!cell) return;

  cell.dataset['score'] = String(newScore);
  cell.className = 'heatmap-cell';
  if (dateStr === habitToday) cell.classList.add('today');
  const scoreData: number | undefined = hasRecord ? newScore : undefined;
  const cls = getScoreClass(scoreData);
  if (cls) cell.classList.add(cls);

  const scoreInt = Math.round(newScore);
  const scoreLabel = newScore !== 0 ? `\nスコア: ${scoreInt}` : (hasRecord ? '\nスコア: 0（相殺）' : '');
  cell.title = `${formatDateLabel(dateStr)}${scoreLabel}`;
}

/** トグル後にヒートマップセルをスコア差分で更新する */
function applyHeatmapDelta(dateStr: string, scoreDelta: number, nowCompleted: boolean): void {
  const cell = document.querySelector<HTMLElement>(`.heatmap-cell[data-date="${dateStr}"]`);
  if (!cell) return;

  const prevScore = parseFloat(cell.dataset['score'] ?? '0');
  const newScore = prevScore + scoreDelta;
  // レコードがあるかどうか: 今回達成 or 既存レコードがある
  const prevHasRecord = cell.dataset['hasRecord'] === '1';
  const hasRecord = nowCompleted || prevHasRecord;
  if (nowCompleted) cell.dataset['hasRecord'] = '1';

  updateHeatmapCell(dateStr, newScore, hasRecord);
}

/** 週ビューのセル（ドット）と達成数バッジをトグル後に更新する */
function updateWeekCell(habitId: string, dateStr: string, completed: boolean, color: string): void {
  const row = document.querySelector<HTMLElement>(`tr[data-habit-id="${habitId}"]`);
  if (!row) return;

  const headers = Array.from(document.querySelectorAll<HTMLElement>('th[data-week-date]'));
  const colIndex = headers.findIndex(h => h.dataset['weekDate'] === dateStr);
  if (colIndex < 0) return;

  // セル: +1 は習慣名列の分
  const cells = row.querySelectorAll('td');
  const cell = cells[colIndex + 1];
  if (!cell) return;

  const dot = cell.querySelector<HTMLElement>('.week-dot');
  if (!dot) return;

  if (completed) {
    dot.classList.add('done');
    dot.style.background = color;
    dot.style.border = 'none';
  } else {
    dot.classList.remove('done');
    dot.style.background = '';
    dot.style.border = '';
  }

  // 達成数バッジを更新
  const allDots = Array.from(row.querySelectorAll('.week-dot'));
  const doneCount = allDots.filter(d => d.classList.contains('done')).length;
  const badge = row.querySelector<HTMLElement>('.week-goal-badge');
  if (badge) {
    const currentText = badge.textContent?.trim() ?? '';
    const slash = currentText.indexOf('/');
    if (slash >= 0) {
      const goal = currentText.slice(slash + 1);
      badge.textContent = `${doneCount}/${goal}`;
      const goalNum = parseInt(goal, 10);
      badge.className = `week-goal-badge badge ${goalNum > 0 && doneCount >= goalNum ? 'badge-success' : 'badge-secondary'}`;
    } else {
      badge.textContent = String(doneCount);
    }
  }
}

// ---- AJAX トグル ----

async function doToggle(habitId: string, dateStr: string, coefficient: string): Promise<{ completed: boolean; score_delta: number } | null> {
  const tokenEl = document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]');
  const csrfToken = tokenEl?.value ?? '';

  const resp = await fetch('/carbohydratepro/habits/toggle/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
    body: `habit_id=${habitId}&date=${dateStr}&coefficient=${coefficient}`,
  });
  const data = await resp.json() as { completed?: boolean; score_delta?: number; error?: string };
  if (data.error) { console.error('toggle error:', data.error); return null; }
  return { completed: data.completed ?? false, score_delta: data.score_delta ?? 0 };
}

function moveCard(card: HTMLElement, toCompleted: boolean): void {
  const undoneList = document.getElementById('undoneList');
  const doneList = document.getElementById('doneList');
  if (!undoneList || !doneList) return;

  card.dataset['completed'] = toCompleted ? '1' : '0';
  if (toCompleted) {
    card.classList.add('done');
    if (!card.querySelector('.done-icon')) {
      const icon = document.createElement('i');
      icon.className = 'fas fa-check done-icon';
      card.querySelector('.habit-card-main')?.appendChild(icon);
    }
    doneList.appendChild(card);
  } else {
    card.classList.remove('done');
    card.querySelector('.done-icon')?.remove();
    undoneList.appendChild(card);
  }
}

// ---- カードスワイプ ----

const SWIPE_THRESHOLD = 60;

// カードが横スワイプ中かどうかを示すフラグ（パネル切替の誤作動防止）
let isCardDragging = false;

function getCardCoefficient(card: HTMLElement): string {
  const slider = card.querySelector<HTMLInputElement>('.coeff-slider');
  return slider ? slider.value : '1';
}

/** スライダー操作中かどうかを判定 */
function isSliderInteraction(target: EventTarget | null): boolean {
  if (!target) return false;
  const el = target as HTMLElement;
  return el.classList.contains('coeff-slider') || el.closest('.coeff-slider-wrap') !== null;
}

function attachCardSwipe(card: HTMLElement): void {
  let startX = 0;
  let startY = 0;
  let isDragging = false;
  let isVertical = false;   // 縦スクロール中フラグ
  let directionLocked = false; // 方向確定フラグ

  const leftHint = card.querySelector<HTMLElement>('.habit-card-swipe-hint.left');
  const rightHint = card.querySelector<HTMLElement>('.habit-card-swipe-hint.right');

  function onStart(x: number, y: number, target: EventTarget | null): boolean {
    // スライダー操作中はスワイプ無効
    if (isSliderInteraction(target)) return false;
    startX = x;
    startY = y;
    isDragging = false;
    isVertical = false;
    directionLocked = false;
    return true;
  }

  function onMove(x: number, y: number): void {
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
    if (isVertical) return;

    // 完了状態に応じてスライド方向を制限（完了済み→左のみ、未完了→右のみ）
    const completed = card.dataset['completed'] === '1';
    if (completed && dx > 0) return;
    if (!completed && dx < 0) return;

    if (!isDragging && absDx > 8) {
      isDragging = true;
      isCardDragging = true; // パネル切替の誤作動防止
    }
    if (!isDragging) return;

    card.style.transform = `translateX(${dx}px)`;
    const ratio = Math.min(absDx / SWIPE_THRESHOLD, 1);
    if (leftHint) leftHint.style.opacity = dx < 0 ? String(ratio) : '0';
    if (rightHint) rightHint.style.opacity = dx > 0 ? String(ratio) : '0';
  }

  async function onEnd(x: number): Promise<void> {
    const dx = x - startX;
    card.style.transform = '';
    if (leftHint) leftHint.style.opacity = '0';
    if (rightHint) rightHint.style.opacity = '0';
    if (!isDragging || isVertical) return;
    isDragging = false;

    const completed = card.dataset['completed'] === '1';
    const shouldComplete = dx > SWIPE_THRESHOLD;
    const shouldUncomplete = dx < -SWIPE_THRESHOLD;
    const coeff = getCardCoefficient(card);
    const dateStr = card.dataset['date'] ?? habitSelectedDate;

    if (shouldComplete && !completed) {
      const res = await doToggle(card.dataset['habitId'] ?? '', dateStr, coeff);
      if (res) {
        moveCard(card, true);
        applyHeatmapDelta(dateStr, res.score_delta, true);
        updateWeekCell(card.dataset['habitId'] ?? '', dateStr, true, card.dataset['color'] ?? '');
      }
    } else if (shouldUncomplete && completed) {
      const res = await doToggle(card.dataset['habitId'] ?? '', dateStr, coeff);
      if (res) {
        moveCard(card, false);
        applyHeatmapDelta(dateStr, res.score_delta, false);
        updateWeekCell(card.dataset['habitId'] ?? '', dateStr, false, card.dataset['color'] ?? '');
      }
    }
  }

  card.addEventListener('touchstart', (e: TouchEvent) => {
    onStart(e.touches[0].clientX, e.touches[0].clientY, e.target);
  }, { passive: true });
  card.addEventListener('touchmove', (e: TouchEvent) => {
    onMove(e.touches[0].clientX, e.touches[0].clientY);
    if (isDragging && !isVertical) e.preventDefault();
  }, { passive: false });
  card.addEventListener('touchend', (e: TouchEvent) => onEnd(e.changedTouches[0].clientX));

  card.addEventListener('mousedown', (e: MouseEvent) => {
    if (!onStart(e.clientX, e.clientY, e.target)) return;
    const onUp = (ev: MouseEvent): void => {
      onEnd(ev.clientX);
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('mousemove', onMv);
    };
    const onMv = (ev: MouseEvent): void => onMove(ev.clientX, ev.clientY);
    document.addEventListener('mousemove', onMv);
    document.addEventListener('mouseup', onUp);
  });
}

// ---- 係数スライダー（カード内） ----

function attachCardSlider(card: HTMLElement): void {
  const slider = card.querySelector<HTMLInputElement>('.coeff-slider');
  const label = card.querySelector<HTMLElement>('.coeff-val');
  if (!slider || !label) return;

  const isPositive = slider.dataset['positive'] !== 'false';
  slider.addEventListener('input', () => {
    label.textContent = `${isPositive ? '+' : '-'}${slider.value}`;
  });
}

// ---- タブ & パネルスワイプ ----

let currentPanel = 0;
const PANEL_COUNT = 3;

function updateWrapHeight(): void {
  const wrap = document.getElementById('habitPanelsWrap');
  const panels = document.querySelectorAll<HTMLElement>('.habit-panel');
  if (!wrap || panels.length === 0) return;
  const panel = panels[currentPanel];
  if (panel) wrap.style.height = `${panel.scrollHeight}px`;
}

function switchPanel(index: number): void {
  if (index < 0 || index >= PANEL_COUNT) return;
  currentPanel = index;
  const panels = document.getElementById('habitPanels');
  if (panels) panels.style.transform = `translateX(-${index * 100}%)`;
  document.querySelectorAll<HTMLElement>('.habit-tab').forEach((tab, i) => {
    tab.classList.toggle('active', i === index);
  });
  // パネル切り替え後に高さを更新
  setTimeout(updateWrapHeight, 50);
}

function attachPanelSwipe(): void {
  const wrap = document.getElementById('habitPanelsWrap');
  if (!wrap) return;
  let startX = 0;
  let startY = 0;
  let dragging = false;

  wrap.addEventListener('touchstart', (e: TouchEvent) => {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    dragging = false;
    isCardDragging = false; // 新しいタッチ開始時にフラグをリセット
  }, { passive: true });
  wrap.addEventListener('touchmove', (e: TouchEvent) => {
    const dx = e.touches[0].clientX - startX;
    const dy = e.touches[0].clientY - startY;
    if (!dragging && Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) dragging = true;
  }, { passive: true });
  wrap.addEventListener('touchend', (e: TouchEvent) => {
    // カードスワイプ中はパネル切替しない
    if (!dragging || isCardDragging) return;
    const dx = e.changedTouches[0].clientX - startX;
    if (dx < -50) switchPanel(currentPanel + 1);
    else if (dx > 50) switchPanel(currentPanel - 1);
  });
}

// ---- 日付ナビ（date picker） ----

async function loadDateStatus(dateStr: string): Promise<void> {
  try {
    const resp = await fetch(`/carbohydratepro/habits/status/?date=${dateStr}`);
    if (!resp.ok) { console.error('status fetch error:', resp.status); return; }
    const json = await resp.json() as { status: Array<Record<string, unknown>>; date: string };

    const undoneList = document.getElementById('undoneList');
    const doneList = document.getElementById('doneList');
    if (!undoneList || !doneList) return;
    undoneList.innerHTML = '';
    doneList.innerHTML = '';

    for (const item of json.status) {
      const card = buildCard(item, dateStr);
      attachCardSwipe(card);
      attachCardSlider(card);
      if (item['completed']) doneList.appendChild(card);
      else undoneList.appendChild(card);
    }

    // date picker の値を更新
    const picker = document.getElementById('datePickerInput') as HTMLInputElement | null;
    if (picker) picker.value = dateStr;

    // パネル高さ更新
    updateWrapHeight();
  } catch (err) {
    console.error('loadDateStatus error:', err);
  }
}

function buildCard(item: Record<string, unknown>, dateStr: string): HTMLElement {
  const completed = item['completed'] as boolean;
  const isPositive = item['is_positive'] as boolean;
  const defaultCoeff = item['default_coefficient'] as number;
  const usedCoeff = item['used_coefficient'] as number;
  const color = item['color'] as string;
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

async function loadYearHeatmap(year: number | null): Promise<void> {
  try {
    const url = year !== null
      ? `/carbohydratepro/habits/heatmap/?year=${year}`
      : '/carbohydratepro/habits/heatmap/';
    const resp = await fetch(url);
    if (!resp.ok) { console.error('heatmap fetch error:', resp.status); return; }
    const data = await resp.json() as Record<string, number>;
    renderHeatmap(data, habitToday, year);
    // 年ビューのパネル高さ更新
    setTimeout(updateWrapHeight, 50);
  } catch (err) {
    console.error('loadYearHeatmap error:', err);
  }
}

// ---- 日付詳細表示（週/年ビューのクリック） ----

async function showDayDetail(dateStr: string): Promise<void> {
  const section = document.getElementById('dayDetailSection');
  const content = document.getElementById('dayDetailContent');
  const titleEl = document.getElementById('dayDetailDate');
  if (!section || !content) return;

  try {
    const resp = await fetch(`/carbohydratepro/habits/status/?date=${dateStr}`);
    if (!resp.ok) return;
    const json = await resp.json() as { status: Array<Record<string, unknown>>; date: string; error?: string };
    if (json.error) return;

    if (titleEl) titleEl.textContent = formatDateLabel(dateStr);
    content.innerHTML = '';

    if (json.status.length === 0) {
      content.innerHTML = '<p class="text-muted small mb-0">習慣が登録されていません。</p>';
    } else {
      for (const item of json.status) {
        const completed = item['completed'] as boolean;
        const color = item['color'] as string;
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
  } catch (err) {
    console.error('showDayDetail error:', err);
  }
}

function closeDayDetail(): void {
  const section = document.getElementById('dayDetailSection');
  if (section) section.style.display = 'none';
}

// ---- モーダル（追加/編集） ----

function habitSelectPositive(prefix: string, positive: boolean): void {
  const posBtn = document.getElementById(`${prefix}PositiveBtn`);
  const negBtn = document.getElementById(`${prefix}NegativeBtn`);
  const input = document.getElementById(`${prefix}IsPositive`) as HTMLInputElement | null;
  if (posBtn) posBtn.classList.toggle('selected', positive);
  if (negBtn) negBtn.classList.toggle('selected', !positive);
  if (input) input.value = positive ? 'true' : 'false';
}

function habitFreqChanged(prefix: string): void {
  const freq = (document.getElementById(`${prefix}Frequency`) as HTMLSelectElement | null)?.value;
  const weeklyField = document.getElementById(`${prefix}WeeklyGoalField`);
  const monthlyField = document.getElementById(`${prefix}MonthlyGoalField`);
  if (weeklyField) weeklyField.classList.toggle('hidden', freq !== 'weekly');
  if (monthlyField) monthlyField.classList.toggle('hidden', freq !== 'monthly');
}

function openEditHabit(
  id: number,
  title: string,
  frequency: string,
  coefficient: number,
  isPositive: boolean,
  weeklyGoal: number,
  monthlyGoal: number,
): void {
  const form = document.getElementById('editHabitForm') as HTMLFormElement | null;
  if (!form) return;

  form.action = `/carbohydratepro/habits/edit/${id}/`;
  const titleEl = document.getElementById('editTitle') as HTMLInputElement | null;
  const freqEl = document.getElementById('editFrequency') as HTMLSelectElement | null;
  const coeffEl = document.getElementById('editCoefficient') as HTMLInputElement | null;
  const coeffValEl = document.getElementById('editCoeffVal');
  const weeklyEl = document.getElementById('editWeeklyGoal') as HTMLInputElement | null;
  const monthlyEl = document.getElementById('editMonthlyGoal') as HTMLInputElement | null;

  if (titleEl) titleEl.value = title;
  if (freqEl) { freqEl.value = frequency; habitFreqChanged('edit'); }
  if (coeffEl) coeffEl.value = String(coefficient);
  if (coeffValEl) coeffValEl.textContent = String(coefficient);
  if (weeklyEl) weeklyEl.value = String(weeklyGoal);
  if (monthlyEl) monthlyEl.value = String(monthlyGoal);

  habitSelectPositive('edit', isPositive);

  // 頻度に応じた目標フィールド表示
  const weeklyField = document.getElementById('editWeeklyGoalField');
  const monthlyField = document.getElementById('editMonthlyGoalField');
  if (weeklyField) weeklyField.classList.toggle('hidden', frequency !== 'weekly');
  if (monthlyField) monthlyField.classList.toggle('hidden', frequency !== 'monthly');

  ($('#editHabitModal') as JQuery).modal('show');
}

function initHabitListInteractions(): void {
  document.querySelectorAll<HTMLElement>('.habit-mgmt-item.lp-delete-item').forEach(item => {
    const habitId = parseInt(item.dataset['habitId'] ?? '0', 10);
    if (!habitId) return;

    let lastTapTime = 0;
    let suppressClick = false;
    let clickCount = 0;
    let clickTimer: ReturnType<typeof setTimeout> | null = null;

    function openEdit(): void {
      const title = item.dataset['habitTitle'] ?? '';
      const frequency = item.dataset['habitFrequency'] ?? 'daily';
      const coefficient = parseFloat(item.dataset['habitCoefficient'] ?? '1');
      const isPositive = item.dataset['habitIsPositive'] === 'true';
      const weeklyGoal = parseInt(item.dataset['habitWeeklyGoal'] ?? '0', 10);
      const monthlyGoal = parseInt(item.dataset['habitMonthlyGoal'] ?? '0', 10);
      openEditHabit(habitId, title, frequency, coefficient, isPositive, weeklyGoal, monthlyGoal);
    }

    item.addEventListener('touchend', (e: TouchEvent) => {
      const target = e.target as HTMLElement;
      if (isInteractiveTarget(target) || item.classList.contains('delete-pending')) return;
      const now = Date.now();
      if (now - lastTapTime < 400) {
        e.preventDefault();
        suppressClick = true;
        lastTapTime = 0;
        openEdit();
      } else {
        lastTapTime = now;
      }
    }, { passive: false });

    item.addEventListener('click', (e: MouseEvent) => {
      if (suppressClick) { suppressClick = false; return; }
      const target = e.target as HTMLElement;
      if (isInteractiveTarget(target) || item.classList.contains('delete-pending')) return;
      clickCount++;
      if (clickCount === 1) {
        clickTimer = setTimeout(() => { clickCount = 0; }, 400);
      } else if (clickCount >= 2) {
        if (clickTimer !== null) clearTimeout(clickTimer);
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
  if (!document.getElementById('habitHeatmap')) return;
  renderHeatmap(heatmapData, habitToday, habitSelectedYear);

  // 初期高さ設定
  setTimeout(updateWrapHeight, 100);

  // 習慣カード
  document.querySelectorAll<HTMLElement>('.habit-card').forEach(card => {
    attachCardSwipe(card);
    attachCardSlider(card);
  });

  // タブ
  document.querySelectorAll<HTMLElement>('.habit-tab').forEach((tab, i) => {
    tab.addEventListener('click', () => switchPanel(i));
  });
  attachPanelSwipe();

  // 日付 picker
  const datePicker = document.getElementById('datePickerInput') as HTMLInputElement | null;
  if (datePicker) {
    datePicker.addEventListener('change', () => {
      const d = datePicker.value;
      if (d) loadDateStatus(d);
    });
  }

  // 年ナビ
  document.querySelectorAll<HTMLElement>('.year-nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const yearStr = btn.dataset['year'] ?? '';
      const year = yearStr ? parseInt(yearStr.replace(/,/g, ''), 10) : null;
      loadYearHeatmap(year);
      document.querySelectorAll<HTMLElement>('.year-nav-btn').forEach(b => {
        b.classList.toggle('btn-primary', b.dataset['year'] === yearStr);
        b.classList.toggle('btn-outline-secondary', b.dataset['year'] !== yearStr);
      });
    });
  });

  // 週ビュー: 日付ヘッダークリックで詳細表示
  document.querySelectorAll<HTMLElement>('[data-week-date]').forEach(el => {
    el.addEventListener('click', () => {
      const d = el.dataset['weekDate'] ?? '';
      if (d) showDayDetail(d);
    });
  });

  // 年ビュー: ヒートマップセルクリックで詳細表示（イベント委譲）
  const heatmapContainer = document.getElementById('habitHeatmap');
  if (heatmapContainer) {
    heatmapContainer.addEventListener('click', (e: Event) => {
      const cell = (e.target as HTMLElement).closest<HTMLElement>('.heatmap-cell[data-date]');
      if (cell && cell.dataset['date']) showDayDetail(cell.dataset['date']);
    });
  }
});
