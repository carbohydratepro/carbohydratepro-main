// 取引管理用JavaScript

// エラーメッセージを表示する関数
function displayFormErrors(errors) {
    // 既存のエラーメッセージをクリア
    $('.field-error').remove();
    
    // 各フィールドのエラーを表示
    for (var fieldName in errors) {
        var field = $('#id_' + fieldName);
        var errorMessages = errors[fieldName];
        
        if (field.length) {
            // エラーメッセージを作成
            var errorHtml = '<div class="field-error text-danger small mt-1">';
            if (Array.isArray(errorMessages)) {
                errorMessages.forEach(function(msg) {
                    errorHtml += msg + '<br>';
                });
            } else {
                errorHtml += errorMessages;
            }
            errorHtml += '</div>';
            
            // フィールドの親要素（form-group）の後に追加
            field.closest('.form-group').append(errorHtml);
            
            // フィールドに赤枠を追加
            field.addClass('is-invalid');
        }
    }
}

// 編集モーダル関連
function openEditModal(transactionId) {
    $.ajax({
        url: '/carbohydratepro/expenses/edit/' + transactionId + '/',
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#editModal .modal-dialog').html(response);
            $('#editModal').modal('show');
            
            // フォーム送信時の処理
            $('#editTransactionForm').on('submit', function(e) {
                e.preventDefault();
                
                // エラー表示をクリア
                $('.field-error').remove();
                $('input, select, textarea').removeClass('is-invalid');
                
                $.ajax({
                    url: $(this).attr('action'),
                    type: 'POST',
                    data: $(this).serialize(),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    success: function(response) {
                        if (response.success) {
                            $('#editModal').modal('hide');
                            location.reload();
                        } else if (response.errors) {
                            displayFormErrors(response.errors);
                        } else {
                            alert('エラーが発生しました。入力内容を確認してください。');
                        }
                    },
                    error: function() {
                        alert('保存に失敗しました。');
                    }
                });
            });
        },
        error: function(xhr, status, error) {
            console.error('Edit modal Ajax error:', {
                status: xhr.status,
                statusText: xhr.statusText,
                responseText: xhr.responseText,
                error: error
            });
            alert('データの読み込みに失敗しました。(ステータス: ' + xhr.status + ')');
        }
    });
}

// 新規作成モーダル関連
function openCreateModal(createUrl) {
    // createUrlが指定されていない場合はデフォルトのURLを使用
    if (!createUrl) {
        createUrl = '/carbohydratepro/expenses/create/';
    }
    
    $.ajax({
        url: createUrl,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            $('#createModal .modal-dialog').html(response);
            $('#createModal').modal('show');
            
            // フォーム送信時の処理
            $('#createTransactionForm').on('submit', function(e) {
                e.preventDefault();
                
                // エラー表示をクリア
                $('.field-error').remove();
                $('input, select, textarea').removeClass('is-invalid');
                
                $.ajax({
                    url: $(this).attr('action'),
                    type: 'POST',
                    data: $(this).serialize(),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    success: function(response) {
                        if (response.success) {
                            $('#createModal').modal('hide');
                            location.reload();
                        } else if (response.errors) {
                            displayFormErrors(response.errors);
                        } else {
                            alert('エラーが発生しました。入力内容を確認してください。');
                        }
                    },
                    error: function() {
                        alert('保存に失敗しました。');
                    }
                });
            });
        },
        error: function(xhr, status, error) {
            console.error('Create modal Ajax error:', {
                status: xhr.status,
                statusText: xhr.statusText,
                responseText: xhr.responseText,
                error: error
            });
            alert('データの読み込みに失敗しました。(ステータス: ' + xhr.status + ')');
        }
    });
}

$(document).ready(function() {
    // 日付フィールドのdatepicker設定
    $('.datepicker').on('click', function() {
        this.showPicker();
    });
    
    // 金額フィールドの整数入力制限
    $('input[name="amount"]').on('input', function() {
        // 小数点が入力された場合は削除
        this.value = this.value.replace(/[^\d]/g, '');
    });
    
    // 金額フィールドのペースト時の処理
    $('input[name="amount"]').on('paste', function(e) {
        setTimeout(function() {
            var input = e.target;
            input.value = input.value.replace(/[^\d]/g, '');
        }, 1);
    });
});

// グラフ初期化関数
function initializeExpenseCharts() {
    if (typeof categoryData === 'undefined' || typeof expenseData === 'undefined' || 
        typeof balanceData === 'undefined' || typeof majorCategoryData === 'undefined') {
        console.warn('Chart data not available');
        return;
    }

    // PC用カテゴリの割合を表す円グラフ
    var ctxPie = document.getElementById('categoryPieChart');
    if (ctxPie) {
        var categoryPieChart = new Chart(ctxPie.getContext('2d'), {
            type: 'pie',
            data: categoryData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'カテゴリ別割合'
                    },
                    legend: {
                        display: categoryData.labels[0] !== 'データなし',
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // PC用支出を表す棒グラフ
    var ctxBar = document.getElementById('expenseBarChart');
    if (ctxBar) {
        // Y軸の最大値を計算（データの最大値と1000の大きい方）
        var maxExpense = Math.max(...expenseData.datasets[0].data, 1000);
        
        var expenseBarChart = new Chart(ctxBar.getContext('2d'), {
            type: 'bar',
            data: expenseData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '日別支出'
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 10,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: maxExpense,
                        grid: {
                            color: 'rgba(255, 99, 132, 0.2)'
                        },
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 5
                        }
                    }
                }
            }
        });
    }

    // モバイル用支出を表す棒グラフ
    var ctxBarMobile = document.getElementById('expenseBarChartMobile');
    if (ctxBarMobile) {
        // Y軸の最大値を計算（データの最大値と1000の大きい方）
        var maxExpenseMobile = Math.max(...expenseData.datasets[0].data, 1000);
        
        var expenseBarChartMobile = new Chart(ctxBarMobile.getContext('2d'), {
            type: 'bar',
            data: expenseData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '日別支出'
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 8,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: maxExpenseMobile,
                        grid: {
                            color: 'rgba(255, 99, 132, 0.2)'
                        },
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 4
                        }
                    }
                }
            }
        });
    }

    // モバイル用メインカテゴリを表すグラフ
    var ctxMajorCategory = document.getElementById('majorCategoryChart');
    if (ctxMajorCategory) {
        var majorCategoryChart = new Chart(ctxMajorCategory.getContext('2d'), {
            type: 'pie',
            data: majorCategoryData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '費用タイプ別割合'
                    },
                    legend: {
                        display: majorCategoryData.labels[0] !== 'データなし',
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // PC用メインカテゴリを表すグラフ
    var ctxMajorCategoryPC = document.getElementById('majorCategoryChartPC');
    if (ctxMajorCategoryPC) {
        var majorCategoryChartPC = new Chart(ctxMajorCategoryPC.getContext('2d'), {
            type: 'pie',
            data: majorCategoryData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '費用タイプ別割合'
                    },
                    legend: {
                        display: majorCategoryData.labels[0] !== 'データなし',
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // PC用所持金の遷移を表す折れ線グラフ
    var ctxLine = document.getElementById('balanceLineChart');
    if (ctxLine) {
        var balanceLineChart = new Chart(ctxLine.getContext('2d'), {
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
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        order: 1
                    },
                    {
                        label: '基準線 (0円)',
                        data: Array(balanceData.labels.length).fill(0),
                        borderColor: 'rgba(255, 0, 0, 0.5)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false,
                        order: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                },
                plugins: {
                    title: {
                        display: true,
                        text: '日別収支推移'
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 10,
                        }
                    },
                    y: {
                        grid: {
                            color: function(context) {
                                // 0の線を強調表示
                                if (context.tick.value === 0) {
                                    return 'rgba(255, 0, 0, 0.3)';
                                }
                                return 'rgba(255, 99, 132, 0.2)';
                            },
                            lineWidth: function(context) {
                                // 0の線を太くする
                                if (context.tick.value === 0) {
                                    return 2;
                                }
                                return 1;
                            }
                        },
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 5
                        }
                    }
                }
            }
        });

        // Y軸範囲を事前に計算
        const originalData = balanceData.datasets[0].data;
        const minValue = Math.min(...originalData);
        const maxValue = Math.max(...originalData);
        
        // 自然な目盛りを生成する関数
        function getNiceScale(min, max) {
            const range = max - min;
            const roughStep = range / 5; // 5程度の目盛りを目指す
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
            
            const niceMin = Math.floor(min / niceStep) * niceStep;
            const niceMax = Math.ceil(max / niceStep) * niceStep;
            
            return { min: niceMin, max: niceMax, step: niceStep };
        }
        
        const scale = getNiceScale(minValue, maxValue);
        // 余裕を持たせるため、さらに1ステップ分拡張
        const yMin = Math.min(scale.min - scale.step, 0); // 0を下限として考慮し、さらに余裕を持たせる
        const yMax = scale.max + scale.step;
        
        // Y軸範囲を固定
        balanceLineChart.options.scales.y.min = yMin;
        balanceLineChart.options.scales.y.max = yMax;
        balanceLineChart.options.scales.y.ticks.stepSize = scale.step;
        balanceLineChart.update('none');

        // アニメーション: ドットを一つずつ表示
        let currentIndex = 0;
        
        function addNextPoint() {
            if (currentIndex < originalData.length) {
                balanceLineChart.data.datasets[0].data.push(originalData[currentIndex]);
                balanceLineChart.update('none'); // アニメーションなしで更新
                currentIndex++;
                setTimeout(addNextPoint, 30); // 30msごとに次のポイントを追加
            }
        }
        
        setTimeout(addNextPoint, 10); // 10ms後にアニメーション開始
    }

    // モバイル用所持金の遷移を表す折れ線グラフ
    var ctxLineMobile = document.getElementById('balanceLineChartMobile');
    if (ctxLineMobile) {
        var balanceLineChartMobile = new Chart(ctxLineMobile.getContext('2d'), {
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
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        order: 1
                    },
                    {
                        label: '基準線 (0円)',
                        data: Array(balanceData.labels.length).fill(0),
                        borderColor: 'rgba(255, 0, 0, 0.5)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false,
                        order: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                },
                plugins: {
                    title: {
                        display: true,
                        text: '日別収支推移'
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 8,
                        }
                    },
                    y: {
                        grid: {
                            color: function(context) {
                                // 0の線を強調表示
                                if (context.tick.value === 0) {
                                    return 'rgba(255, 0, 0, 0.3)';
                                }
                                return 'rgba(255, 99, 132, 0.2)';
                            },
                            lineWidth: function(context) {
                                // 0の線を太くする
                                if (context.tick.value === 0) {
                                    return 2;
                                }
                                return 1;
                            }
                        },
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 4
                        }
                    }
                }
            }
        });

        // Y軸範囲を事前に計算
        const originalDataMobile = balanceData.datasets[0].data;
        const minValueMobile = Math.min(...originalDataMobile);
        const maxValueMobile = Math.max(...originalDataMobile);
        
        // 自然な目盛りを生成する関数（モバイル用）
        function getNiceScaleMobile(min, max) {
            const range = max - min;
            const roughStep = range / 4; // モバイルでは4程度の目盛りを目指す
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
            
            const niceMin = Math.floor(min / niceStep) * niceStep;
            const niceMax = Math.ceil(max / niceStep) * niceStep;
            
            return { min: niceMin, max: niceMax, step: niceStep };
        }
        
        const scaleMobile = getNiceScaleMobile(minValueMobile, maxValueMobile);
        // 余裕を持たせるため、さらに1ステップ分拡張
        const yMinMobile = Math.min(scaleMobile.min - scaleMobile.step, 0); // 0を下限として考慮し、さらに余裕を持たせる
        const yMaxMobile = scaleMobile.max + scaleMobile.step;
        
        // Y軸範囲を固定
        balanceLineChartMobile.options.scales.y.min = yMinMobile;
        balanceLineChartMobile.options.scales.y.max = yMaxMobile;
        balanceLineChartMobile.options.scales.y.ticks.stepSize = scaleMobile.step;
        balanceLineChartMobile.update('none');

        // アニメーション: ドットを一つずつ表示
        let currentIndexMobile = 0;
        
        function addNextPointMobile() {
            if (currentIndexMobile < originalDataMobile.length) {
                balanceLineChartMobile.data.datasets[0].data.push(originalDataMobile[currentIndexMobile]);
                balanceLineChartMobile.update('none'); // アニメーションなしで更新
                currentIndexMobile++;
                setTimeout(addNextPointMobile, 30); // 30msごとに次のポイントを追加
            }
        }
        
        setTimeout(addNextPointMobile, 10); // 10ms後にアニメーション開始
    }
}

// フィルター変更時の処理
function initializeExpenseFilters() {
    var filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('change', function() {
            // 検索クエリも保持
            const currentUrl = new URL(window.location);
            const targetDateInput = document.getElementById('target_date');
            if (targetDateInput) {
                currentUrl.searchParams.set('target_date', targetDateInput.value);
                window.location.href = currentUrl.toString();
            }
        });
    }
}