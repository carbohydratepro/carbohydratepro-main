// 取引管理用JavaScript

interface TransactionModalResponse {
  success: boolean;
  errors?: Record<string, string | string[]>;
}

interface NiceScale {
  min: number;
  max: number;
  step: number;
}

// エラーメッセージを表示する関数
function displayFormErrors(errors: Record<string, string | string[]>): void {
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

            field.closest('.form-group')?.appendChild(errorDiv);
            field.classList.add('is-invalid');
        }
    }
}

// フォームデータをURLSearchParams形式に変換
function serializeForm(form: HTMLFormElement): string {
    return new URLSearchParams(new FormData(form) as unknown as Record<string, string>).toString();
}

// Ajax モーダルフォーム送信の共通処理
async function submitModalForm(form: HTMLFormElement, modalSelector: string): Promise<void> {
    // エラー表示をクリア
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll<HTMLElement>('input, select, textarea').forEach(el => el.classList.remove('is-invalid'));

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: serializeForm(form),
        });
        const data: TransactionModalResponse = await response.json();

        if (data.success) {
            $(modalSelector).modal('hide');
            location.reload();
        } else if (data.errors) {
            displayFormErrors(data.errors);
        } else {
            alert('エラーが発生しました。入力内容を確認してください。');
        }
    } catch {
        alert('保存に失敗しました。');
    }
}

// 編集モーダル関連
async function openEditModal(transactionId: string): Promise<void> {
    try {
        const response = await fetch(`/carbohydratepro/expenses/edit/${transactionId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#editModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
        $('#editModal').modal('show');

        const form = document.getElementById('editTransactionForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitModalForm(form, '#editModal');
            });
        }
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error('Edit modal error:', error);
        alert(`データの読み込みに失敗しました。(${message})`);
    }
}

// 新規作成モーダル関連
async function openCreateModal(createUrl = '/carbohydratepro/expenses/create/'): Promise<void> {
    try {
        const response = await fetch(createUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        const modalDialog = document.querySelector<HTMLElement>('#createModal .modal-dialog');
        if (modalDialog) modalDialog.innerHTML = html;
        $('#createModal').modal('show');

        const form = document.getElementById('createTransactionForm');
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                submitModalForm(form, '#createModal');
            });
        }
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error('Create modal error:', error);
        alert(`データの読み込みに失敗しました。(${message})`);
    }
}

// 入力フィールドの初期化
document.addEventListener('DOMContentLoaded', () => {
    // 日付フィールドのdatepicker設定
    document.querySelectorAll<HTMLInputElement>('.datepicker').forEach(el => {
        el.addEventListener('click', () => el.showPicker());
    });

    // 金額フィールドの整数入力制限
    document.querySelectorAll<HTMLInputElement>('input[name="amount"]').forEach(el => {
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
function getNiceScale(min: number, max: number, tickCount = 5): NiceScale {
    const range = max - min;
    const roughStep = range / tickCount;
    const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const normalizedStep = roughStep / magnitude;

    let niceStep: number;
    if (normalizedStep < 1.5) {
        niceStep = 1 * magnitude;
    } else if (normalizedStep < 3) {
        niceStep = 2 * magnitude;
    } else if (normalizedStep < 7) {
        niceStep = 5 * magnitude;
    } else {
        niceStep = 10 * magnitude;
    }

    return {
        min: Math.floor(min / niceStep) * niceStep,
        max: Math.ceil(max / niceStep) * niceStep,
        step: niceStep,
    };
}

// 折れ線グラフのアニメーション表示
function animateLineChart(chart: Chart, originalData: number[], delay = 30): void {
    let currentIndex = 0;
    const addNextPoint = (): void => {
        if (currentIndex < originalData.length) {
            chart.data.datasets[0].data.push(originalData[currentIndex]);
            chart.update('none');
            currentIndex++;
            setTimeout(addNextPoint, delay);
        }
    };
    setTimeout(addNextPoint, 10);
}

// 折れ線グラフの共通オプション生成
function createLineChartConfig(
    balanceData: ChartData,
    maxTicksLimitX: number,
    maxTicksLimitY: number,
    hoverRadius: number,
): ChartConfig {
    return {
        type: 'line',
        data: {
            labels: balanceData.labels,
            datasets: [
                {
                    label: balanceData.datasets[0].label,
                    data: [],
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
            animation: { duration: 2000, easing: 'easeInOutQuart' },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: { display: true, text: '日別収支推移' },
                legend: { display: true, position: 'bottom' },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: (ctx: ChartTooltipContext) => {
                            if (ctx.dataset.label === '基準線 (0円)') return '';
                            const value = ctx.parsed.y;
                            const formatted = value.toLocaleString('ja-JP');
                            return `${ctx.dataset.label ?? ''}: ${formatted}円`;
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
                        color: (ctx: ChartScaleContext) => ctx.tick.value === 0 ? 'rgba(255, 0, 0, 0.3)' : 'rgba(255, 99, 132, 0.2)',
                        lineWidth: (ctx: ChartScaleContext) => ctx.tick.value === 0 ? 2 : 1,
                    },
                    ticks: { autoSkip: true, maxTicksLimit: maxTicksLimitY },
                },
            },
        },
    };
}

// 折れ線グラフの初期化とアニメーション開始
function initializeLineChart(
    canvasId: string,
    balanceData: ChartData,
    maxTicksX: number,
    maxTicksY: number,
    hoverRadius: number,
    tickCount: number,
): void {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement | null;
    if (!canvas) return;

    if (canvasId.includes('Mobile')) {
        if (canvas.parentElement) canvas.parentElement.style.height = '300px';
        canvas.style.height = '300px';
        canvas.height = 300;
    }

    const config = createLineChartConfig(balanceData, maxTicksX, maxTicksY, hoverRadius);
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const chart = new Chart(ctx, config);

    const originalData = balanceData.datasets[0].data;
    const minValue = Math.min(...originalData);
    const maxValue = Math.max(...originalData);
    const scale = getNiceScale(minValue, maxValue, tickCount);

    chart.options.scales!.y!.min = Math.min(scale.min - scale.step, 0);
    chart.options.scales!.y!.max = scale.max + scale.step;
    chart.options.scales!.y!.ticks!.stepSize = scale.step;
    chart.update('none');

    animateLineChart(chart, originalData);
}

// グラフ初期化関数
function initializeExpenseCharts(): void {
    if (typeof categoryData === 'undefined' || typeof expenseData === 'undefined' ||
        typeof balanceData === 'undefined' || typeof majorCategoryData === 'undefined') {
        console.warn('Chart data not available');
        return;
    }

    // カテゴリ円グラフ
    const ctxPie = document.getElementById('categoryPieChart') as HTMLCanvasElement | null;
    if (ctxPie) {
        const pieCtx = ctxPie.getContext('2d');
        if (pieCtx) {
            new Chart(pieCtx, {
                type: 'pie',
                data: categoryData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'カテゴリ別割合' },
                        legend: { display: false },
                    },
                },
            });
        }
    }

    // 棒グラフ共通オプション生成
    const createBarConfig = (data: ChartData, maxTicksX: number, maxTicksY: number): ChartConfig => ({
        type: 'bar',
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: '日別支出' } },
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
    const ctxBar = document.getElementById('expenseBarChart') as HTMLCanvasElement | null;
    if (ctxBar) {
        const barCtx = ctxBar.getContext('2d');
        if (barCtx) new Chart(barCtx, createBarConfig(expenseData, 10, 5));
    }

    // モバイル用棒グラフ
    const ctxBarMobile = document.getElementById('expenseBarChartMobile') as HTMLCanvasElement | null;
    if (ctxBarMobile) {
        if (ctxBarMobile.parentElement) ctxBarMobile.parentElement.style.height = '250px';
        ctxBarMobile.style.height = '250px';
        ctxBarMobile.height = 250;
        const barMobileCtx = ctxBarMobile.getContext('2d');
        if (barMobileCtx) new Chart(barMobileCtx, createBarConfig(expenseData, 8, 4));
    }

    // メインカテゴリ円グラフ共通オプション
    const majorCategoryConfig: ChartConfig = {
        type: 'pie',
        data: majorCategoryData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: '費用タイプ別割合' },
                legend: { display: false },
            },
        },
    };

    // モバイル用メインカテゴリ
    const ctxMajorCategory = document.getElementById('majorCategoryChart') as HTMLCanvasElement | null;
    if (ctxMajorCategory) {
        const majorCtx = ctxMajorCategory.getContext('2d');
        if (majorCtx) new Chart(majorCtx, majorCategoryConfig);
    }

    // PC用メインカテゴリ
    const ctxMajorCategoryPC = document.getElementById('majorCategoryChartPC') as HTMLCanvasElement | null;
    if (ctxMajorCategoryPC) {
        const majorPCCtx = ctxMajorCategoryPC.getContext('2d');
        if (majorPCCtx) new Chart(majorPCCtx, majorCategoryConfig);
    }

    // PC用折れ線グラフ
    initializeLineChart('balanceLineChart', balanceData, 10, 5, 6, 5);

    // モバイル用折れ線グラフ
    initializeLineChart('balanceLineChartMobile', balanceData, 8, 4, 8, 4);
}

// 年ビュー: 月別収支グラフを描画
function initializeYearlyCharts(): void {
    if (typeof monthlyData === 'undefined') return;

    const canvas = document.getElementById('monthlyBarChart') as HTMLCanvasElement | null;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    new Chart(ctx, {
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
                        label: (ctx: ChartTooltipContext) => {
                            const value = ctx.parsed.y;
                            return `${ctx.dataset.label ?? ''}: ¥${value.toLocaleString('ja-JP')}`;
                        },
                    },
                },
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
function initializeExpenseFilters(): void {
    // filterForm は HTML 側の onchange で直接サブミットするため処理なし
}

// ページ読み込み後にグラフとフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('monthlyBarChart')) {
        initializeYearlyCharts();
    } else {
        initializeExpenseCharts();
    }
    initializeExpenseFilters();
});
