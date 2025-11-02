function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');


// メッセージダイアログを自動表示
window.addEventListener('DOMContentLoaded', function() {
    const dialog = document.getElementById('messageDialog');
    if (dialog) {
        // まず表示してから、少し遅延させてクラスを追加（アニメーション用）
        dialog.style.display = 'flex';
        setTimeout(function() {
            dialog.classList.add('show');
        }, 10);
        
        // 5秒後に自動的に閉じる
        setTimeout(function() {
            closeMessageDialog();
        }, 5000);
    }
});

// ダイアログを閉じる
function closeMessageDialog() {
    const dialog = document.getElementById('messageDialog');
    if (dialog) {
        dialog.classList.remove('show');
        setTimeout(function() {
            dialog.style.display = 'none';
        }, 300);
    }
}

// 背景クリックでダイアログを閉じる
document.addEventListener('click', function(e) {
    const dialog = document.getElementById('messageDialog');
    if (dialog && e.target === dialog) {
        closeMessageDialog();
    }
});

// ESCキーでダイアログを閉じる
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeMessageDialog();
    }
});
