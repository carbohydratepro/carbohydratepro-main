let demoLoginClosing = false;

/** デモの更新・編集操作は、通信や楽観的更新より前にここで終了する。 */
function requireDemoLogin(): boolean {
    if (!document.getElementById('demoSignupModal')) return false;
    const show = (): void => { $('#demoSignupModal').modal('show'); };
    if (demoLoginClosing) {
        $('#demoSignupModal').off('hidden.bs.modal.demoReopen').one('hidden.bs.modal.demoReopen', show);
        return true;
    }
    const open = $('.modal.show').not('#demoSignupModal');
    if (open.length) {
        open.last().one('hidden.bs.modal', show);
        open.modal('hide');
    } else {
        show();
    }
    return true;
}

document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('demoSignupModal')) return;
    $('#demoSignupModal').on('hide.bs.modal', () => { demoLoginClosing = true; })
        .on('hidden.bs.modal', () => { demoLoginClosing = false; });
    // HTML内の登録・編集・削除フォームも、通常モーダルを開く前に止める。
    $(document).on('show.bs.modal', '.modal', function (event) {
        if (this.id === 'demoSignupModal' || !this.querySelector('form[method="post"]')) return;
        event.preventDefault();
        requireDemoLogin();
    });
    document.addEventListener('submit', event => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() === 'get') return;
        event.preventDefault();
        event.stopImmediatePropagation();
        requireDemoLogin();
    }, true);
    document.addEventListener('click', event => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        const button = target.closest('button, input');
        const submits = (button instanceof HTMLButtonElement || button instanceof HTMLInputElement)
            && button.type === 'submit' && button.form !== null && button.form.method.toLowerCase() !== 'get';
        if (!submits && !target.closest('.lp-delete-overlay, .kanban-task-delete-overlay, [data-demo-login], [onclick*=".submit("]')) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        requireDemoLogin();
    }, true);
});
