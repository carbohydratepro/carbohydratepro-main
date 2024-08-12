from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import TransactionForm, PaymentMethodForm, CategoryForm
from .models import Transaction

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
    if request.method == 'POST':
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
    else:
        payment_form = PaymentMethodForm(prefix='payment')
        purpose_form = CategoryForm(prefix='purpose')
    return render(request, 'app/settings.html', {
        'payment_form': payment_form,
        'purpose_form': purpose_form
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
