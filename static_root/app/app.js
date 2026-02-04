function getCookie(name) {
    if (!document.cookie || document.cookie === '') return null;
    const found = document.cookie.split(';')
        .map(c => c.trim())
        .find(c => c.startsWith(`${name}=`));
    return found ? decodeURIComponent(found.substring(name.length + 1)) : null;
}

const csrftoken = getCookie('csrftoken');

// メッセージダイアログを自動表示
document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('messageDialog');
    if (dialog) {
        dialog.style.display = 'flex';
        setTimeout(() => dialog.classList.add('show'), 10);
        setTimeout(() => closeMessageDialog(), 5000);
    }
});

// ダイアログを閉じる
function closeMessageDialog() {
    const dialog = document.getElementById('messageDialog');
    if (dialog) {
        dialog.classList.remove('show');
        setTimeout(() => { dialog.style.display = 'none'; }, 300);
    }
}

// 背景クリックでダイアログを閉じる
document.addEventListener('click', (e) => {
    const dialog = document.getElementById('messageDialog');
    if (dialog && e.target === dialog) {
        closeMessageDialog();
    }
});

// ESCキーでダイアログを閉じる
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeMessageDialog();
    }
});
