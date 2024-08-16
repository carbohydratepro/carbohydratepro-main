from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import TransactionForm, PaymentMethodForm, CategoryForm
from .models import Transaction, PaymentMethod, Category

@login_required
def index(request):
    transactions = Transaction.objects.filter(user=request.user)  # ユーザーに紐づくデータのみ表示
    return render(request, 'app/index.html', {'transactions': transactions})

@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('index')  # 投稿後は一覧画面にリダイレクト
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'app/create_transaction.html', {'form': form})

@login_required
def settings_view(request):
    payment_form = PaymentMethodForm(prefix='payment')
    purpose_form = CategoryForm(prefix='purpose')

    # 編集対象のオブジェクト（支払方法・使用用途）
    edit_payment_instance = None
    edit_purpose_instance = None

    # 処理の分岐
    if request.method == 'POST':
        if 'payment_id' in request.POST:  # 支払方法の編集または削除
            payment = get_object_or_404(PaymentMethod, id=request.POST.get('payment_id'), user=request.user)
            if 'edit_payment' in request.POST:  # 支払方法の編集
                payment_form = PaymentMethodForm(request.POST, instance=payment, prefix='payment')
                if payment_form.is_valid():
                    payment_form.save()
                    return redirect('settings')
                edit_payment_instance = payment
            elif 'delete_payment' in request.POST:  # 支払方法の削除
                payment.delete()
                return redirect('settings')

        elif 'purpose_id' in request.POST:  # 使用用途の編集または削除
            purpose = get_object_or_404(Category, id=request.POST.get('purpose_id'), user=request.user)
            if 'edit_purpose' in request.POST:  # 使用用途の編集
                purpose_form = CategoryForm(request.POST, instance=purpose, prefix='purpose')
                if purpose_form.is_valid():
                    purpose_form.save()
                    return redirect('settings')
                edit_purpose_instance = purpose
            elif 'delete_purpose' in request.POST:  # 使用用途の削除
                purpose.delete()
                return redirect('settings')

        else:  # 新規作成フォームの処理
            payment_form = PaymentMethodForm(request.POST, prefix='payment')
            purpose_form = CategoryForm(request.POST, prefix='purpose')
            if payment_form.is_valid():
                new_payment_method = payment_form.save(commit=False)
                new_payment_method.user = request.user
                new_payment_method.save()
            if purpose_form.is_valid():
                new_purpose = purpose_form.save(commit=False)
                new_purpose.user = request.user
                new_purpose.save()
            return redirect('settings')

    # ユーザーに関連する支払方法と使用用途を取得
    payments = PaymentMethod.objects.filter(user=request.user)
    purposes = Category.objects.filter(user=request.user)

    return render(request, 'app/settings.html', {
        'payment_form': payment_form,
        'purpose_form': purpose_form,
        'payments': payments,
        'purposes': purposes,
        'edit_payment_instance': edit_payment_instance,
        'edit_purpose_instance': edit_purpose_instance,
    })

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'app/edit_transaction.html', {'form': form})

@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('index')
    return render(request, 'app/confirm_delete.html', {'transaction': transaction})

