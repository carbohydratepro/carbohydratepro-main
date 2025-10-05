// 取引関連のJavaScript

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