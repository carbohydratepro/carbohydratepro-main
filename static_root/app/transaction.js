// 取引管理用JavaScript

// エラーメッセージを表示する関数
function displayFormErrors(errors) {
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
async function openEditModal(transactionId) {
    try {
        const response = await fetch(`/carbohydratepro/expenses/edit/${transactionId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#editModal .modal-dialog').innerHTML = html;
        $('#editModal').modal('show');

        const form = document.getElementById('editTransactionForm');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            submitModalForm(form, '#editModal');
        });
    } catch (error) {
        console.error('Edit modal error:', error);
        alert(`データの読み込みに失敗しました。(${error.message})`);
    }
}

// 新規作成モーダル関連
async function openCreateModal(createUrl = '/carbohydratepro/expenses/create/') {
    try {
        const response = await fetch(createUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error(`ステータス: ${response.status}`);
        const html = await response.text();

        document.querySelector('#createModal .modal-dialog').innerHTML = html;
        $('#createModal').modal('show');

        const form = document.getElementById('createTransactionForm');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            submitModalForm(form, '#createModal');
        });
    } catch (error) {
        console.error('Create modal error:', error);
        alert(`データの読み込みに失敗しました。(${error.message})`);
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
    const range = max - min;
    const roughStep = range / tickCount;
    const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const normalizedStep = roughStep / magnitude;

    let niceStep;
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
function animateLineChart(chart, originalData, delay = 30) {
    let currentIndex = 0;
    const addNextPoint = () => {
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
function createLineChartConfig(balanceData, maxTicksLimitX, maxTicksLimitY, hoverRadius) {
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
            plugins: {
                title: { display: true, text: '日別収支推移' },
                legend: { display: true, position: 'bottom' },
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

// 折れ線グラフの初期化とアニメーション開始
function initializeLineChart(canvasId, balanceData, maxTicksX, maxTicksY, hoverRadius, tickCount) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (canvasId.includes('Mobile')) {
        canvas.parentElement.style.height = '300px';
        canvas.style.height = '300px';
        canvas.height = 300;
    }

    const config = createLineChartConfig(balanceData, maxTicksX, maxTicksY, hoverRadius);
    const chart = new Chart(canvas.getContext('2d'), config);

    const originalData = balanceData.datasets[0].data;
    const minValue = Math.min(...originalData);
    const maxValue = Math.max(...originalData);
    const scale = getNiceScale(minValue, maxValue, tickCount);

    chart.options.scales.y.min = Math.min(scale.min - scale.step, 0);
    chart.options.scales.y.max = scale.max + scale.step;
    chart.options.scales.y.ticks.stepSize = scale.step;
    chart.update('none');

    animateLineChart(chart, originalData);
}

// グラフ初期化関数
function initializeExpenseCharts() {
    if (typeof categoryData === 'undefined' || typeof expenseData === 'undefined' ||
        typeof balanceData === 'undefined' || typeof majorCategoryData === 'undefined') {
        console.warn('Chart data not available');
        return;
    }

    // カテゴリ円グラフ
    const ctxPie = document.getElementById('categoryPieChart');
    if (ctxPie) {
        new Chart(ctxPie.getContext('2d'), {
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

    // 棒グラフ共通オプション生成
    const createBarConfig = (data, maxTicksX, maxTicksY) => ({
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
    const ctxBar = document.getElementById('expenseBarChart');
    if (ctxBar) {
        new Chart(ctxBar.getContext('2d'), createBarConfig(expenseData, 10, 5));
    }

    // モバイル用棒グラフ
    const ctxBarMobile = document.getElementById('expenseBarChartMobile');
    if (ctxBarMobile) {
        ctxBarMobile.parentElement.style.height = '250px';
        ctxBarMobile.style.height = '250px';
        ctxBarMobile.height = 250;
        new Chart(ctxBarMobile.getContext('2d'), createBarConfig(expenseData, 8, 4));
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
        },
    };

    // モバイル用メインカテゴリ
    const ctxMajorCategory = document.getElementById('majorCategoryChart');
    if (ctxMajorCategory) {
        new Chart(ctxMajorCategory.getContext('2d'), majorCategoryConfig);
    }

    // PC用メインカテゴリ
    const ctxMajorCategoryPC = document.getElementById('majorCategoryChartPC');
    if (ctxMajorCategoryPC) {
        new Chart(ctxMajorCategoryPC.getContext('2d'), majorCategoryConfig);
    }

    // PC用折れ線グラフ
    initializeLineChart('balanceLineChart', balanceData, 10, 5, 6, 5);

    // モバイル用折れ線グラフ
    initializeLineChart('balanceLineChartMobile', balanceData, 8, 4, 8, 4);
}

// フィルター変更時の処理
function initializeExpenseFilters() {
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('change', () => {
            const currentUrl = new URL(window.location);
            const targetDateInput = document.getElementById('target_date');
            if (targetDateInput) {
                currentUrl.searchParams.set('target_date', targetDateInput.value);
                window.location.href = currentUrl.toString();
            }
        });
    }
}

// ページ読み込み後にグラフとフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeExpenseCharts();
    initializeExpenseFilters();
});
