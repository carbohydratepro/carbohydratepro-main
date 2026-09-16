"use strict";
// 取引管理用JavaScript
let expenseListAbortController = null;
function buildExpenseFilterUrl(name, value) {
    if (!value || value === 'データなし')
        return null;
    const url = new URL(window.location.href);
    url.searchParams.delete('page');
    if (name === 'category' && value.startsWith('exclude:')) {
        url.searchParams.delete('category');
        url.searchParams.delete('exclude_category');
        value.slice('exclude:'.length).split(',').filter(Boolean).forEach(categoryId => {
            url.searchParams.append('exclude_category', categoryId);
        });
        return url;
    }
    if (name === 'category')
        url.searchParams.delete('exclude_category');
    if (name === 'payment_method')
        url.searchParams.delete('exclude_payment_method');
    url.searchParams.delete(name);
    url.searchParams.append(name, value);
    return url;
}
function syncExpenseFilterForm(url) {
    const form = document.getElementById('expenseSearchFilterForm');
    if (!(form instanceof HTMLFormElement))
        return;
    const repeatedFields = [
        'category',
        'exclude_category',
        'payment_method',
        'exclude_payment_method',
    ];
    repeatedFields.forEach(name => {
        const selected = new Set(url.searchParams.getAll(name));
        form.querySelectorAll(`input[name="${name}"]`).forEach(input => {
            input.checked = selected.has(input.value);
        });
    });
    ['search', 'major_category', 'transaction_type', 'date', 'target_date', 'view_mode'].forEach(name => {
        var _a;
        const field = form.elements.namedItem(name);
        if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) {
            field.value = (_a = url.searchParams.get(name)) !== null && _a !== void 0 ? _a : '';
        }
    });
}
async function updateExpenseList(url) {
    var _a;
    const listRegion = document.getElementById('transactionListRegion');
    if (!(listRegion instanceof HTMLElement))
        return;
    const bulkContainer = document.querySelector('[data-bulk-container]');
    if (bulkContainer === null || bulkContainer === void 0 ? void 0 : bulkContainer.classList.contains('bulk-mode')) {
        (_a = bulkContainer.querySelector('[data-bulk-toggle]')) === null || _a === void 0 ? void 0 : _a.click();
    }
    expenseListAbortController === null || expenseListAbortController === void 0 ? void 0 : expenseListAbortController.abort();
    const controller = new AbortController();
    expenseListAbortController = controller;
    listRegion.setAttribute('aria-busy', 'true');
    const status = document.getElementById('expenseListStatus');
    if (status)
        status.textContent = '記録一覧を更新しています…';
    try {
        const response = await fetch(url.toString(), {
            headers: {
                'Accept': 'text/html',
                'X-Requested-With': 'XMLHttpRequest',
            },
            signal: controller.signal,
        });
        if (!response.ok || response.redirected) {
            throw new Error(`ステータス: ${response.status}`);
        }
        const html = await response.text();
        if (expenseListAbortController !== controller)
            return;
        listRegion.innerHTML = html;
        syncExpenseFilterForm(url);
        window.history.replaceState(null, '', url.toString());
        initLongPressDelete(listRegion);
        initTransactionDoubleClick(listRegion);
        if (status)
            status.textContent = '記録一覧を更新しました。グラフは変更していません。';
        syncExpenseChartFilterButtons(url);
    }
    catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError')
            return;
        console.error('Expense list filter error:', error);
        showToast('取引一覧の絞り込みに失敗しました。', 'error');
        if (status)
            status.textContent = '更新できませんでした。表示中の記録は保持しています。';
    }
    finally {
        if (expenseListAbortController === controller) {
            listRegion.removeAttribute('aria-busy');
            expenseListAbortController = null;
        }
    }
}
function filterExpenseList(name, value) {
    const url = buildExpenseFilterUrl(name, value);
    if (url)
        void updateExpenseList(url);
}
function chartFilterHandler(name, data) {
    return (_event, elements) => {
        var _a, _b, _c, _d;
        const index = (_a = elements[0]) === null || _a === void 0 ? void 0 : _a.index;
        if (index === undefined)
            return;
        const value = (_d = (_c = (_b = data.filterValues) === null || _b === void 0 ? void 0 : _b[index]) !== null && _c !== void 0 ? _c : data.labels[index]) !== null && _d !== void 0 ? _d : '';
        filterExpenseList(name, value);
    };
}
function syncExpenseChartFilterButtons(url) {
    document.querySelectorAll('[data-chart-filter]').forEach(button => {
        var _a, _b;
        const name = (_a = button.dataset['chartFilter']) !== null && _a !== void 0 ? _a : '';
        const value = (_b = button.dataset['filterValue']) !== null && _b !== void 0 ? _b : '';
        const excluded = name === 'category' && value.startsWith('exclude:')
            ? value.slice('exclude:'.length).split(',').filter(Boolean).sort() : [];
        const actualExcluded = url.searchParams.getAll('exclude_category').sort();
        const selected = excluded.length > 0
            ? !url.searchParams.has('category') && JSON.stringify(excluded) === JSON.stringify(actualExcluded)
            : url.searchParams.getAll(name).includes(value);
        button.setAttribute('aria-pressed', String(selected));
    });
}
function initializeExpenseChartFilterButtons() {
    var _a;
    const region = document.getElementById('expenseChartFilters');
    if (!region)
        return;
    const groups = [
        ['カテゴリ', 'category', typeof categoryData === 'undefined' ? undefined : categoryData],
        ['費用タイプ', 'major_category', typeof majorCategoryData === 'undefined' ? undefined : majorCategoryData],
    ];
    groups.forEach(([label, name, data]) => {
        if (!(data === null || data === void 0 ? void 0 : data.labels.length))
            return;
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = `${label}を選ぶ`;
        details.appendChild(summary);
        const buttons = document.createElement('div');
        buttons.className = 'chart-filter-buttons';
        data.labels.forEach((text, index) => {
            var _a, _b;
            const value = (_b = (_a = data.filterValues) === null || _a === void 0 ? void 0 : _a[index]) !== null && _b !== void 0 ? _b : text;
            if (!value || value === 'データなし')
                return;
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-outline-primary btn-sm';
            button.textContent = text;
            button.dataset['chartFilter'] = name;
            button.dataset['filterValue'] = value;
            button.addEventListener('click', () => filterExpenseList(name, value));
            buttons.appendChild(button);
        });
        if (buttons.childElementCount) {
            details.appendChild(buttons);
            region.appendChild(details);
        }
    });
    syncExpenseChartFilterButtons(new URL(window.location.href));
    (_a = document.getElementById('transactionListRegion')) === null || _a === void 0 ? void 0 : _a.addEventListener('click', event => {
        if (!(event.target instanceof Element) || !event.target.closest('[data-clear-expense-filters]'))
            return;
        const url = new URL(window.location.href);
        ['search', 'category', 'exclude_category', 'payment_method', 'exclude_payment_method', 'major_category', 'transaction_type', 'date', 'page'].forEach(key => url.searchParams.delete(key));
        void updateExpenseList(url);
    });
}
// エラーメッセージを表示する関数
function displayFormErrors(errors) {
    var _a;
    // 既存のエラーメッセージをクリア
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    // 各フィールドのエラーを表示
    for (const fieldName in errors) {
        const field = document.getElementById(`id_${fieldName}`);
        const errorMessages = errors[fieldName];
        if (field) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-danger small mt-1';
            errorDiv.innerHTML = Array.isArray(errorMessages)
                ? errorMessages.join('<br>')
                : errorMessages;
            (_a = field.closest('.form-group')) === null || _a === void 0 ? void 0 : _a.appendChild(errorDiv);
            field.classList.add('is-invalid');
        }
    }
}
// フォームデータをURLSearchParams形式に変換
function serializeForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}
// Ajax モーダルフォーム送信の共通処理
async function submitModalForm(form, modalSelector) {
    // エラー表示をクリア
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('input, select, textarea').forEach(el => el.classList.remove('is-invalid'));
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: serializeForm(form),
        });
        const data = await response.json();
        if (data.success) {
            $(modalSelector).modal('hide');
            location.reload();
        }
        else if (data.errors) {
            displayFormErrors(data.errors);
        }
        else {
            alert('エラーが発生しました。入力内容を確認してください。');
        }
    }
    catch (_a) {
        alert('保存に失敗しました。');
    }
}
// 編集モーダル関連
async function openEditModal(transactionId) {
    try {
        const response = await fetch(`/carbohydratepro/expenses/edit/${transactionId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#editModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#editModal').modal('show');
        const form = document.getElementById('editTransactionForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitModalForm(form, '#editModal');
            });
        }
    }
    catch (error) {
        // デモモードは fetch を意図的に reject する。サインアップモーダルは既に
        // 表示済みなので、エラー通知は出さない。
        if (error instanceof Error && error.message === 'demo')
            return;
        const message = error instanceof Error ? error.message : String(error);
        console.error('Edit modal error:', error);
        alert(`データの読み込みに失敗しました。(${message})`);
    }
}
// 新規作成モーダル関連
async function openCreateModal(createUrl = '/carbohydratepro/expenses/create/') {
    try {
        const response = await fetch(createUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok)
            throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();
        const modalDialog = document.querySelector('#createModal .modal-dialog');
        if (modalDialog)
            modalDialog.innerHTML = html;
        $('#createModal').modal('show');
        const form = document.getElementById('createTransactionForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitModalForm(form, '#createModal');
            });
        }
    }
    catch (error) {
        // デモモードは fetch を意図的に reject する。サインアップモーダルは既に
        // 表示済みなので、エラー通知は出さない。
        if (error instanceof Error && error.message === 'demo')
            return;
        const message = error instanceof Error ? error.message : String(error);
        console.error('Create modal error:', error);
        alert(`データの読み込みに失敗しました。(${message})`);
    }
}
// 入力フィールドの初期化
document.addEventListener('DOMContentLoaded', () => {
    // 日付フィールドのdatepicker設定
    document.querySelectorAll('.datepicker').forEach(el => {
        el.addEventListener('click', () => el.showPicker());
    });
    // 金額フィールドの整数入力制限
    document.querySelectorAll('input[name="amount"]').forEach(el => {
        el.addEventListener('input', () => {
            el.value = el.value.replace(/[^\d]/g, '');
        });
        el.addEventListener('paste', () => {
            setTimeout(() => {
                el.value = el.value.replace(/[^\d]/g, '');
            }, 1);
        });
    });
});
// 自然な目盛りを生成する関数
function getNiceScale(min, max, tickCount = 5) {
    min = Number.isFinite(min) ? Math.min(min, 0) : 0;
    max = Number.isFinite(max) ? Math.max(max, 0) : 1;
    const range = max - min || 1;
    const roughStep = range / tickCount;
    const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const normalizedStep = roughStep / magnitude;
    let niceStep;
    if (normalizedStep < 1.5) {
        niceStep = 1 * magnitude;
    }
    else if (normalizedStep < 3) {
        niceStep = 2 * magnitude;
    }
    else if (normalizedStep < 7) {
        niceStep = 5 * magnitude;
    }
    else {
        niceStep = 10 * magnitude;
    }
    return {
        min: Math.floor(min / niceStep) * niceStep,
        max: Math.ceil(max / niceStep) * niceStep,
        step: niceStep,
    };
}
// 折れ線グラフの共通オプション生成
function createLineChartConfig(balanceData, maxTicksLimitX, maxTicksLimitY, hoverRadius) {
    return {
        type: 'line',
        data: {
            labels: balanceData.labels,
            datasets: [
                {
                    label: balanceData.datasets[0].label,
                    data: [...balanceData.datasets[0].data],
                    fill: balanceData.datasets[0].fill,
                    borderColor: balanceData.datasets[0].borderColor,
                    backgroundColor: balanceData.datasets[0].backgroundColor || 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: hoverRadius,
                    order: 1,
                },
                {
                    label: '基準線 (0円)',
                    data: Array(balanceData.labels.length).fill(0),
                    borderColor: 'rgba(255, 0, 0, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false,
                    order: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            onClick: chartFilterHandler('date', balanceData),
            plugins: {
                title: { display: true, text: '日別収支推移' },
                legend: { display: true, position: 'bottom' },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: (ctx) => {
                            var _a;
                            if (ctx.dataset.label === '基準線 (0円)')
                                return '';
                            const value = ctx.parsed.y;
                            const formatted = value.toLocaleString('ja-JP');
                            return `${(_a = ctx.dataset.label) !== null && _a !== void 0 ? _a : ''}: ${formatted}円`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: 'category',
                    ticks: { autoSkip: true, maxTicksLimit: maxTicksLimitX },
                },
                y: {
                    grid: {
                        color: (ctx) => ctx.tick.value === 0 ? 'rgba(255, 0, 0, 0.3)' : 'rgba(255, 99, 132, 0.2)',
                        lineWidth: (ctx) => ctx.tick.value === 0 ? 2 : 1,
                    },
                    ticks: { autoSkip: true, maxTicksLimit: maxTicksLimitY },
                },
            },
        },
    };
}
// 折れ線グラフは全日分を一度に描画する
function initializeLineChart(canvasId, balanceData, maxTicksX, maxTicksY, hoverRadius, tickCount) {
    const canvas = getPendingExpenseCanvas(canvasId);
    if (!canvas)
        return;
    const config = createLineChartConfig(balanceData, maxTicksX, maxTicksY, hoverRadius);
    const ctx = canvas.getContext('2d');
    if (!ctx)
        return;
    const originalData = balanceData.datasets[0].data;
    const minValue = Math.min(...originalData);
    const maxValue = Math.max(...originalData);
    const scale = getNiceScale(minValue, maxValue, tickCount);
    config.options.scales.y.min = Math.min(scale.min - scale.step, 0);
    config.options.scales.y.max = scale.max + scale.step;
    config.options.scales.y.ticks.stepSize = scale.step;
    registerExpenseChart(ctx, config);
}
// 土日色付け状態（localStorage で永続化）
let weekendColorEnabled = localStorage.getItem('weekendColorEnabled') === 'true';
// 土日判定
function isWeekend(dateStr) {
    const date = new Date(dateStr);
    const day = date.getDay();
    return day === 0 || day === 6;
}
// 棒グラフ用の色配列を生成（土日色付けON/OFFに応じる）
function buildBarColors(labels) {
    const normalColor = '#FF6384';
    const weekendColor = 'rgba(255, 165, 0, 0.75)';
    return labels.map(label => (weekendColorEnabled && isWeekend(label)) ? weekendColor : normalColor);
}
// 土日色付けトグル（設定画面から呼ばれる場合などに使用）
function toggleWeekendColor() {
    weekendColorEnabled = !weekendColorEnabled;
    localStorage.setItem('weekendColorEnabled', String(weekendColorEnabled));
    // 棒グラフの色を更新
    if (activeBarCharts.length > 0 && typeof expenseData !== 'undefined') {
        const colors = buildBarColors(expenseData.labels);
        activeBarCharts.forEach(chart => {
            chart.data.datasets[0].backgroundColor = colors;
            chart.update();
        });
    }
}
// 棒グラフのチャートインスタンスを保持
const activeBarCharts = [];
const activeExpenseCharts = [];
function registerExpenseChart(ctx, config) {
    const chart = new Chart(ctx, Object.assign(Object.assign({}, config), { options: Object.assign(Object.assign({}, config.options), { animation: false }) }));
    activeExpenseCharts.push(chart);
    return chart;
}
// CSSで隠れているPC/スマホ用・折りたたみ内のグラフは表示時まで生成しない。
// 既存インスタンスは保持し、絞り込みや再展開ではデータを作り直さない。
function getPendingExpenseCanvas(id) {
    const canvas = document.getElementById(id);
    if (!(canvas instanceof HTMLCanvasElement) || !canvas.getClientRects().length || Chart.getChart(canvas)) {
        return null;
    }
    return canvas;
}
function initializeVisibleExpenseCharts() {
    if (document.getElementById('monthlyBarChart'))
        initializeYearlyCharts();
    else
        initializeExpenseCharts();
}
function initializeExpenseChartCollapses() {
    document.querySelectorAll('.expense-chart-collapse').forEach(panel => {
        $(panel).on('shown.bs.collapse', () => {
            initializeVisibleExpenseCharts();
            activeExpenseCharts.forEach(chart => {
                if (panel.contains(chart.canvas))
                    chart.resize();
            });
        });
    });
    window.matchMedia('(min-width: 768px)').addEventListener('change', () => {
        initializeVisibleExpenseCharts();
    });
}
let expenseComparisonChart = null;
const EXPENSE_COMPARISON_STORAGE_KEY = 'expenseComparisonVisible';
function initializeExpenseComparisonChart() {
    if (expenseComparisonChart || typeof comparisonData === 'undefined')
        return;
    const canvas = document.getElementById('expenseComparisonChart');
    const ctx = canvas === null || canvas === void 0 ? void 0 : canvas.getContext('2d');
    if (!ctx)
        return;
    expenseComparisonChart = registerExpenseChart(ctx, {
        type: 'bar',
        data: comparisonData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'bottom' },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: (tooltipContext) => {
                            var _a;
                            const label = (_a = tooltipContext.dataset.label) !== null && _a !== void 0 ? _a : '';
                            const value = Math.round(tooltipContext.parsed.y).toLocaleString('ja-JP');
                            return `${label}: ¥${value}`;
                        },
                    },
                },
            },
            scales: {
                x: { type: 'category' },
                y: { beginAtZero: true },
            },
        },
    });
}
function setExpenseComparisonVisible(visible) {
    const panel = document.getElementById('expenseComparisonPanel');
    const button = document.getElementById('expenseComparisonToggle');
    const label = document.getElementById('expenseComparisonToggleLabel');
    if (!(panel instanceof HTMLElement) || !(button instanceof HTMLButtonElement))
        return;
    panel.hidden = !visible;
    button.setAttribute('aria-expanded', String(visible));
    button.classList.toggle('btn-primary', visible);
    button.classList.toggle('btn-outline-primary', !visible);
    if (label)
        label.textContent = visible ? '比較を閉じる' : '先月・全期間平均と比較';
    if (visible)
        initializeExpenseComparisonChart();
    localStorage.setItem(EXPENSE_COMPARISON_STORAGE_KEY, String(visible));
}
function initializeExpenseComparisonToggle() {
    const button = document.getElementById('expenseComparisonToggle');
    if (!(button instanceof HTMLButtonElement))
        return;
    const initiallyVisible = localStorage.getItem(EXPENSE_COMPARISON_STORAGE_KEY) === 'true';
    setExpenseComparisonVisible(initiallyVisible);
    button.addEventListener('click', () => {
        setExpenseComparisonVisible(button.getAttribute('aria-expanded') !== 'true');
    });
}
// グラフ初期化関数
function initializeExpenseCharts() {
    if (typeof categoryData === 'undefined' || typeof expenseData === 'undefined' ||
        typeof balanceData === 'undefined' || typeof majorCategoryData === 'undefined') {
        console.warn('Chart data not available');
        return;
    }
    // カテゴリ円グラフ
    const ctxPie = getPendingExpenseCanvas('categoryPieChart');
    if (ctxPie) {
        const pieCtx = ctxPie.getContext('2d');
        if (pieCtx) {
            registerExpenseChart(pieCtx, {
                type: 'pie',
                data: categoryData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'カテゴリ別割合' },
                        legend: { display: false },
                    },
                    onClick: chartFilterHandler('category', categoryData),
                },
            });
        }
    }
    const ctxPiePC = getPendingExpenseCanvas('categoryPieChartPC');
    if (ctxPiePC) {
        const piePCCtx = ctxPiePC.getContext('2d');
        if (piePCCtx) {
            registerExpenseChart(piePCCtx, {
                type: 'pie',
                data: categoryData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'カテゴリ別割合' },
                        legend: { display: false },
                    },
                    onClick: chartFilterHandler('category', categoryData),
                },
            });
        }
    }
    // 棒グラフ用データを土日色付け状態に応じて準備
    const barColors = buildBarColors(expenseData.labels);
    const expenseDataWithColors = {
        labels: expenseData.labels,
        datasets: [Object.assign(Object.assign({}, expenseData.datasets[0]), { backgroundColor: barColors })],
    };
    // 棒グラフ共通オプション生成
    const createBarConfig = (data, maxTicksX, maxTicksY) => ({
        type: 'bar',
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: '日別支出' } },
            onClick: chartFilterHandler('date', data),
            scales: {
                x: { type: 'category', ticks: { autoSkip: true, maxTicksLimit: maxTicksX } },
                y: {
                    beginAtZero: true,
                    max: Math.max(...data.datasets[0].data, 1000),
                    grid: { color: 'rgba(255, 99, 132, 0.2)' },
                    ticks: { autoSkip: true, maxTicksLimit: maxTicksY },
                },
            },
        },
    });
    // PC用棒グラフ
    const ctxBar = getPendingExpenseCanvas('expenseBarChart');
    if (ctxBar) {
        const barCtx = ctxBar.getContext('2d');
        if (barCtx) {
            const chart = registerExpenseChart(barCtx, createBarConfig(expenseDataWithColors, 10, 5));
            activeBarCharts.push(chart);
        }
    }
    // モバイル用棒グラフ
    const ctxBarMobile = getPendingExpenseCanvas('expenseBarChartMobile');
    if (ctxBarMobile) {
        const barMobileCtx = ctxBarMobile.getContext('2d');
        if (barMobileCtx) {
            const chart = registerExpenseChart(barMobileCtx, createBarConfig(expenseDataWithColors, 8, 4));
            activeBarCharts.push(chart);
        }
    }
    // メインカテゴリ円グラフ共通オプション
    const majorCategoryConfig = {
        type: 'pie',
        data: majorCategoryData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: '費用タイプ別割合' },
                legend: { display: false },
            },
            onClick: chartFilterHandler('major_category', majorCategoryData),
        },
    };
    // モバイル用メインカテゴリ
    const ctxMajorCategory = getPendingExpenseCanvas('majorCategoryChart');
    if (ctxMajorCategory) {
        const majorCtx = ctxMajorCategory.getContext('2d');
        if (majorCtx)
            registerExpenseChart(majorCtx, majorCategoryConfig);
    }
    // PC用メインカテゴリ
    const ctxMajorCategoryPC = getPendingExpenseCanvas('majorCategoryChartPC');
    if (ctxMajorCategoryPC) {
        const majorPCCtx = ctxMajorCategoryPC.getContext('2d');
        if (majorPCCtx)
            registerExpenseChart(majorPCCtx, majorCategoryConfig);
    }
    // PC用折れ線グラフ
    initializeLineChart('balanceLineChart', balanceData, 10, 5, 6, 5);
    // モバイル用折れ線グラフ
    initializeLineChart('balanceLineChartMobile', balanceData, 8, 4, 8, 4);
}
// 年ビュー: 月別収支グラフを描画
function initializeYearlyCharts() {
    var _a;
    if (typeof monthlyData === 'undefined')
        return;
    const canvas = getPendingExpenseCanvas('monthlyBarChart');
    if (!canvas)
        return;
    const ctx = canvas.getContext('2d');
    if (!ctx)
        return;
    const year = (_a = canvas.dataset['year']) !== null && _a !== void 0 ? _a : '';
    registerExpenseChart(ctx, {
        type: 'bar',
        data: monthlyData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: '月別収支グラフ' },
                legend: { display: true, position: 'bottom' },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: (ctx) => {
                            var _a;
                            const value = ctx.parsed.y;
                            return `${(_a = ctx.dataset.label) !== null && _a !== void 0 ? _a : ''}: ¥${value.toLocaleString('ja-JP')}`;
                        },
                    },
                },
            },
            onClick: (_event, elements) => {
                var _a;
                const index = (_a = elements[0]) === null || _a === void 0 ? void 0 : _a.index;
                if (index === undefined || !year)
                    return;
                const month = String(index + 1).padStart(2, '0');
                const url = new URL(window.location.href);
                url.searchParams.set('view_mode', 'month');
                url.searchParams.set('target_date', `${year}-${month}`);
                url.searchParams.delete('page');
                void updateExpenseList(url);
            },
            scales: {
                x: { type: 'category' },
                y: {
                    beginAtZero: true,
                    ticks: { autoSkip: true, maxTicksLimit: 6 },
                },
            },
        },
    });
}
// フィルター変更時の処理（filterFormはonchange="this.form.submit()"で処理するため不要）
function initializeExpenseFilters() {
    document.querySelectorAll('input[data-filter-key]').forEach(input => {
        input.addEventListener('change', () => {
            var _a;
            if (!input.checked)
                return;
            document.querySelectorAll(`input[data-filter-key="${(_a = input.dataset['filterKey']) !== null && _a !== void 0 ? _a : ''}"]`).forEach(peer => {
                if (peer !== input)
                    peer.checked = false;
            });
        });
    });
}
function initTransactionDoubleClick(container = document) {
    container.querySelectorAll('.lp-delete-item[data-item-id]').forEach(card => {
        var _a;
        const transactionId = (_a = card.dataset['itemId']) !== null && _a !== void 0 ? _a : '';
        if (!transactionId)
            return;
        let clickCount = 0;
        let clickTimer = null;
        card.addEventListener('click', (e) => {
            const target = e.target;
            if (isInteractiveTarget(target) || card.classList.contains('delete-pending'))
                return;
            clickCount++;
            if (clickCount === 1) {
                clickTimer = setTimeout(() => { clickCount = 0; }, 300);
            }
            else if (clickCount >= 2) {
                if (clickTimer !== null)
                    clearTimeout(clickTimer);
                clickCount = 0;
                openEditModal(transactionId);
            }
        });
    });
}
// ページ読み込み後にグラフとフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeVisibleExpenseCharts();
    initializeExpenseFilters();
    initializeExpenseComparisonToggle();
    initializeExpenseChartCollapses();
    initializeExpenseChartFilterButtons();
    initLongPressDelete();
    initTransactionDoubleClick();
});
