// ラベル設定画面用JavaScript

// 豊富なカラーテンプレート（50色）
const COLOR_TEMPLATES = [
    // 赤系
    '#FF6B6B', '#EE5A6F', '#E63946', '#D62828', '#C1121F',
    '#FF4757', '#FF3838', '#FF6348', '#FF7675', '#D63031',
    
    // オレンジ系
    '#FFA500', '#FF8C00', '#FF7F50', '#FF6347', '#FF4500',
    '#F39C12', '#E67E22', '#D35400', '#FDA65D', '#FD9644',
    
    // 黄色系
    '#FFD93D', '#FFEB3B', '#FFC312', '#F9CA24', '#F79F1F',
    '#FDD835', '#FBC02D', '#F9A825', '#F57F17', '#FFE66D',
    
    // 緑系
    '#6BCF7F', '#27AE60', '#2ECC71', '#00D2D3', '#1ABC9C',
    '#16A085', '#26DE81', '#20BF6B', '#4CD137', '#2ECC40',
    
    // 青系
    '#3498DB', '#2980B9', '#5DADE2', '#3867D6', '#4834DF',
    '#1E90FF', '#1890FF', '#2F80ED', '#56CCF2', '#0984E3',
    
    // 紫・ピンク系
    '#9B59B6', '#8E44AD', '#A29BFE', '#6C5CE7', '#BE90D4',
    '#E056FD', '#BF55EC', '#F8B500', '#F78FB3', '#FDA7DF',
    
    // グレー・茶色系
    '#95A5A6', '#7F8C8D', '#636E72', '#2D3436', '#B8860B',
    '#8B4513', '#A0522D', '#CD853F', '#DEB887', '#6C757D'
];

// タブ切り替え
function switchColorTab(tabName, modalId) {
    const modal = document.getElementById(modalId);
    const tabs = modal.querySelectorAll('.color-picker-tab');
    const contents = modal.querySelectorAll('.color-picker-content');
    
    tabs.forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    contents.forEach(content => {
        if (content.dataset.tab === tabName) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// カラーテンプレートの選択
function selectColorTemplate(color, modalId) {
    const modal = document.getElementById(modalId);
    const colorInput = modal.querySelector('input[name="color"]');
    const colorPreview = modal.querySelector('.color-preview');
    const templateItems = modal.querySelectorAll('.color-template-item');
    
    // 選択状態を更新
    templateItems.forEach(item => {
        if (item.dataset.color === color) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
    
    // カラー入力フィールドとプレビューを更新
    colorInput.value = color;
    if (colorPreview) {
        colorPreview.style.backgroundColor = color;
        colorPreview.textContent = color;
    }
}

// カスタムカラーピッカーの変更
function updateCustomColor(input, modalId) {
    const modal = document.getElementById(modalId);
    const colorPreview = modal.querySelector('.color-preview');
    const templateItems = modal.querySelectorAll('.color-template-item');
    
    // テンプレートの選択を解除
    templateItems.forEach(item => {
        item.classList.remove('selected');
    });
    
    // プレビューを更新
    if (colorPreview) {
        colorPreview.style.backgroundColor = input.value;
        colorPreview.textContent = input.value;
    }
}

// カラーテンプレートグリッドを生成
function generateColorTemplateGrid(containerId, modalId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    COLOR_TEMPLATES.forEach(color => {
        const item = document.createElement('div');
        item.className = 'color-template-item';
        item.style.backgroundColor = color;
        item.dataset.color = color;
        item.title = color;
        item.onclick = () => selectColorTemplate(color, modalId);
        container.appendChild(item);
    });
}

// モーダルが開かれたときの初期化
function initializeColorPicker(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    const colorInput = modal.querySelector('input[name="color"]');
    const colorPreview = modal.querySelector('.color-preview');
    const templateItems = modal.querySelectorAll('.color-template-item');
    
    // 現在の色がテンプレートにある場合は選択状態にする
    if (colorInput && colorInput.value) {
        const currentColor = colorInput.value.toUpperCase();
        templateItems.forEach(item => {
            if (item.dataset.color.toUpperCase() === currentColor) {
                item.classList.add('selected');
            }
        });
        
        // プレビューを更新
        if (colorPreview) {
            colorPreview.style.backgroundColor = colorInput.value;
            colorPreview.textContent = colorInput.value;
        }
    }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // 新規作成モーダルのカラーテンプレートを生成
    generateColorTemplateGrid('colorTemplateGridCreate', 'createLabelModal');
    
    // 編集モーダルのカラーテンプレートを生成（各ラベルごと）
    document.querySelectorAll('[id^="editLabelModal"]').forEach(modal => {
        const modalId = modal.id;
        const labelId = modalId.replace('editLabelModal', '');
        generateColorTemplateGrid(`colorTemplateGridEdit${labelId}`, modalId);
    });
    
    // モーダルが開かれたときにカラーピッカーを初期化
    $('.modal').on('shown.bs.modal', function() {
        initializeColorPicker(this.id);
    });
});
