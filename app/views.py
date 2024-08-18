from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q
from django.utils.timezone import make_aware
from .forms import TransactionForm, PaymentMethodForm, CategoryForm
from .models import Transaction, PaymentMethod, Category
from datetime import datetime, timedelta

import json

@login_required
def index(request):
    target_date = request.GET.get('target_date', None)

    if target_date:
        target_date = make_aware(datetime.strptime(target_date, '%Y-%m'))
    else:
        # target_dateが指定されていない場合、現在の月をデフォルトとして設定
        target_date = make_aware(datetime.now().replace(day=1))

    start_date = target_date.replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    transactions = Transaction.objects.filter(user=request.user, date__range=(start_date, end_date))

    # 日付範囲の作成（固定された月初から月末）
    date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]

    # グラフ用データの作成
    category_data = transactions.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    major_category_data = transactions.values('major_category').annotate(total=Sum('amount')).order_by('-total')

    expense_data = []
    balance_data = []
    current_balance = 0

    for date in date_range:
        daily_expense = transactions.filter(date__date=date, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        daily_income = transactions.filter(date__date=date, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        current_balance += float(daily_income) - float(daily_expense) # Decimalをfloatに変換
        expense_data.append(float(daily_expense)) # Decimalをfloatに変換
        balance_data.append(float(current_balance)) # Decimalをfloatに変換
    
    category_data_json = json.dumps({
        'labels': [entry['category__name'] for entry in category_data],
        'datasets': [{
            'data': [float(entry['total']) for entry in category_data],  # Decimalをfloatに変換
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56'],
        }]
    })

    major_category_data_json = json.dumps({
        'labels': [entry['major_category'] for entry in major_category_data],
        'datasets': [{
            'data': [float(entry['total']) for entry in major_category_data],  # Decimalをfloatに変換
            'backgroundColor': ['#4BC0C0', '#FF9F40', '#9966FF'],
        }]
    })

    expense_data_json = json.dumps({
        'labels': date_range,
        'datasets': [{
            'label': '支出',
            'data': expense_data,
            'backgroundColor': '#FF6384',
        }]
    })

    balance_data_json = json.dumps({
        'labels': date_range,
        'datasets': [{
            'label': '所持金',
            'data': balance_data,
            'fill': False,
            'borderColor': '#36A2EB',
        }]
    })

    return render(request, 'app/index.html', {
        'transactions': transactions,
        'category_data_json': category_data_json,
        'major_category_data_json': major_category_data_json,
        'expense_data_json': expense_data_json,
        'balance_data_json': balance_data_json,
        'default_target_date': target_date.strftime('%Y-%m')  # 今日の日付をテンプレートに渡す
    })

    
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
    payment_limit = 10
    purpose_limit = 30

    payments = PaymentMethod.objects.filter(user=request.user)
    purposes = Category.objects.filter(user=request.user)

    payment_count = payments.count()
    purpose_count = purposes.count()

    payment_form = PaymentMethodForm(prefix='payment')
    purpose_form = CategoryForm(prefix='purpose')

    edit_payment_instance = None
    edit_purpose_instance = None

    if request.method == 'POST':
        if 'payment_id' in request.POST:
            payment = get_object_or_404(PaymentMethod, id=request.POST.get('payment_id'), user=request.user)
            if 'edit_payment' in request.POST:
                payment_form = PaymentMethodForm(request.POST, instance=payment, prefix='payment')
                if payment_form.is_valid():
                    payment_form.save()
                    return redirect('settings')
                edit_payment_instance = payment
            elif 'delete_payment' in request.POST:
                payment.delete()
                return redirect('settings')

        elif 'purpose_id' in request.POST:
            purpose = get_object_or_404(Category, id=request.POST.get('purpose_id'), user=request.user)
            if 'edit_purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, instance=purpose, prefix='purpose')
                if purpose_form.is_valid():
                    purpose_form.save()
                    return redirect('settings')
                edit_purpose_instance = purpose
            elif 'delete_purpose' in request.POST:
                purpose.delete()
                return redirect('settings')

        else:
            if 'payment' in request.POST:
                payment_form = PaymentMethodForm(request.POST, prefix='payment')
                if payment_count >= payment_limit:
                    payment_form.add_error(None, f"支払方法の登録上限数は{payment_limit}件です。")
                elif payment_form.is_valid():
                    new_payment_method = payment_form.save(commit=False)
                    new_payment_method.user = request.user
                    new_payment_method.save()
                    return redirect('settings')

            elif 'purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, prefix='purpose')
                if purpose_count >= purpose_limit:
                    purpose_form.add_error(None, f"使用用途の登録上限数は{purpose_limit}件です。")
                elif purpose_form.is_valid():
                    new_purpose = purpose_form.save(commit=False)
                    new_purpose.user = request.user
                    new_purpose.save()
                    return redirect('settings')

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

