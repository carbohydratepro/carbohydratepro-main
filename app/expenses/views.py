from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils.timezone import make_aware
from .forms import TransactionForm, PaymentMethodForm, CategoryForm, RecurringPaymentForm
from .models import Transaction, PaymentMethod, Category, RecurringPayment
from datetime import datetime, timedelta, date
import json
from django.http import JsonResponse
from django.core.paginator import Paginator

from project.utils import CHART_COLORS, MAJOR_CATEGORY_LABELS


@login_required
def expenses_list(request):
    target_date = request.GET.get('target_date', None)
    search_query = request.GET.get('search', '')
    per_page_raw = request.GET.get('per_page', '20')
    per_page_options = ['10', '20', '50', '100']
    per_page = int(per_page_raw) if per_page_raw in per_page_options else 20
    
    # 絞り込みパラメータ
    filter_transaction_type = request.GET.get('transaction_type', '')
    filter_major_category = request.GET.get('major_category', '')
    filter_category = request.GET.get('category', '')
    filter_payment_method = request.GET.get('payment_method', '')

    if target_date:
        target_date = make_aware(datetime.strptime(target_date, '%Y-%m'))
    else:
        # target_dateが指定されていない場合、現在の月をデフォルトとして設定
        target_date = make_aware(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))

    start_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)

    transactions_qs = Transaction.objects.filter(
        user=request.user, date__range=(start_date, end_date)
    ).select_related('payment_method', 'category').order_by('-date', '-id')
    
    # 検索機能
    if search_query:
        transactions_qs = transactions_qs.filter(
            Q(purpose__icontains=search_query) |
            Q(purpose_description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(payment_method__name__icontains=search_query)
        )
    
    # 絞り込み機能
    if filter_transaction_type:
        transactions_qs = transactions_qs.filter(transaction_type=filter_transaction_type)
    if filter_major_category:
        transactions_qs = transactions_qs.filter(major_category=filter_major_category)
    if filter_category:
        transactions_qs = transactions_qs.filter(category__id=filter_category)
    if filter_payment_method:
        transactions_qs = transactions_qs.filter(payment_method__id=filter_payment_method)

    transactions_count = transactions_qs.count()
    paginator = Paginator(transactions_qs, per_page)
    page_number = request.GET.get('page')
    transactions_page = paginator.get_page(page_number)
    
    # 絞り込み用のオプション取得
    user_categories = Category.objects.filter(user=request.user)
    user_payment_methods = PaymentMethod.objects.filter(user=request.user)

    # 月合計の収入・支出を計算
    total_income = transactions_qs.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions_qs.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = float(total_income) - float(total_expense)

    # 日付範囲の作成（固定された月初から月末）
    date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]

    # カテゴリグラフ用データの作成（支出のみ、上位5つ + その他）
    expense_transactions = transactions_qs.filter(transaction_type='expense')
    category_data = expense_transactions.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    # カテゴリグラフ：上位5つとその他に分ける
    if category_data.exists():
        top_categories = list(category_data[:5])
        other_total = sum(float(entry['total']) for entry in category_data[5:])
        
        # ラベルを10文字で切り詰める
        category_labels = [entry['category__name'][:10] + ('...' if len(entry['category__name']) > 10 else '') for entry in top_categories]
        category_amounts = [float(entry['total']) for entry in top_categories]

        # 実際のデータ数に応じて色を設定
        category_colors = CHART_COLORS['category'][:len(category_labels)]

        if other_total > 0:
            category_labels.append('その他')
            category_amounts.append(other_total)
            category_colors.append(CHART_COLORS['no_data'])
    else:
        # データがない場合は灰色で表示
        category_labels = ['データなし']
        category_amounts = [1]
        category_colors = [CHART_COLORS['no_data']]
    
    # メインカテゴリを日本語表記で取得（支出のみ、固定3色）
    major_category_data = expense_transactions.values('major_category').annotate(total=Sum('amount')).order_by('-total')

    if major_category_data.exists():
        # 実際のデータ数に応じて色を設定
        major_bg_colors = [CHART_COLORS['major_category'][entry['major_category']] for entry in major_category_data]

        major_category_data_json = json.dumps({
            'labels': [MAJOR_CATEGORY_LABELS[entry['major_category']] for entry in major_category_data],
            'datasets': [{
                'data': [float(entry['total']) for entry in major_category_data],
                'backgroundColor': major_bg_colors,
            }]
        })
    else:
        # データがない場合は灰色で表示
        major_category_data_json = json.dumps({
            'labels': ['データなし'],
            'datasets': [{
                'data': [1],
                'backgroundColor': [CHART_COLORS['no_data']],
            }]
        })

    category_data_json = json.dumps({
        'labels': category_labels,
        'datasets': [{
            'data': category_amounts,
            'backgroundColor': category_colors,
        }]
    })

    expense_data = []
    balance_data = []
    current_balance = 0

    for date in date_range:
        daily_expense = transactions_qs.filter(date__date=date, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        daily_income = transactions_qs.filter(date__date=date, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        current_balance += float(daily_income) - float(daily_expense)  # Decimalをfloatに変換
        expense_data.append(float(daily_expense))  # Decimalをfloatに変換
        balance_data.append(float(current_balance))  # Decimalをfloatに変換

    expense_data_json = json.dumps({
        'labels': date_range,
        'datasets': [{
            'label': '支出',
            'data': expense_data,
            'backgroundColor': CHART_COLORS['expense_bar'],
        }]
    })

    balance_data_json = json.dumps({
        'labels': date_range,
        'datasets': [{
            'label': '所持金',
            'data': balance_data,
            'fill': False,
            'borderColor': CHART_COLORS['balance_line'],
        }]
    })

    # 三桁区切りフォーマット済みの値を作成
    total_income_formatted = '{:,.0f}'.format(float(total_income))
    total_expense_formatted = '{:,.0f}'.format(float(total_expense))
    net_balance_formatted = '{:,.0f}'.format(float(net_balance))
    
    return render(request, 'app/expenses/list.html', {
        'transactions_page': transactions_page,
        'transactions_count': transactions_count,
        'category_data_json': category_data_json,
        'major_category_data_json': major_category_data_json,
        'expense_data_json': expense_data_json,
        'balance_data_json': balance_data_json,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'total_income_formatted': total_income_formatted,
        'total_expense_formatted': total_expense_formatted,
        'net_balance_formatted': net_balance_formatted,
        'target_month': target_date.strftime('%Y年%m月'),
        'search_query': search_query,
        'user_categories': user_categories,
        'user_payment_methods': user_payment_methods,
        'filter_transaction_type': filter_transaction_type,
        'filter_major_category': filter_major_category,
        'filter_category': filter_category,
        'filter_payment_method': filter_payment_method,
        'default_target_date': target_date.strftime('%Y-%m'),  # 今日の日付をテンプレートに渡す
        'per_page': per_page,
        'per_page_options': per_page_options,
    })
    

@login_required
def create_expenses(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('expense_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TransactionForm(user=request.user)
    
    return render(request, 'app/expenses/create_modal.html', {'form': form})


@login_required
def expenses_settings(request):
    payment_limit = 10
    purpose_limit = 10

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
                    return redirect('expenses_settings')
                edit_payment_instance = payment
            elif 'delete_payment' in request.POST:
                payment.delete()
                return redirect('expenses_settings')

        elif 'purpose_id' in request.POST:
            purpose = get_object_or_404(Category, id=request.POST.get('purpose_id'), user=request.user)
            if 'edit_purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, instance=purpose, prefix='purpose')
                if purpose_form.is_valid():
                    purpose_form.save()
                    return redirect('expenses_settings')
                edit_purpose_instance = purpose
            elif 'delete_purpose' in request.POST:
                purpose.delete()
                return redirect('expenses_settings')

        else:
            if 'payment' in request.POST:
                payment_form = PaymentMethodForm(request.POST, prefix='payment')
                if payment_count >= payment_limit:
                    payment_form.add_error(None, f"支払方法の登録上限数は{payment_limit}件です。")
                elif payment_form.is_valid():
                    new_payment_method = payment_form.save(commit=False)
                    new_payment_method.user = request.user
                    new_payment_method.save()
                    return redirect('expenses_settings')

            elif 'purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, prefix='purpose')
                if purpose_count >= purpose_limit:
                    purpose_form.add_error(None, f"使用用途の登録上限数は{purpose_limit}件です。")
                elif purpose_form.is_valid():
                    new_purpose = purpose_form.save(commit=False)
                    new_purpose.user = request.user
                    new_purpose.save()
                    return redirect('expenses_settings')

    return render(request, 'app/expenses/settings.html', {
        'payment_form': payment_form,
        'purpose_form': purpose_form,
        'payments': payments,
        'purposes': purposes,
        'edit_payment_instance': edit_payment_instance,
        'edit_purpose_instance': edit_purpose_instance,
    })


@login_required
def edit_expenses(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('expense_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    return render(request, 'app/expenses/edit_modal.html', {'form': form, 'transaction': transaction})


@login_required
def delete_expenses(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('expense_list')
    return redirect('expense_list')


@login_required
def recurring_payment_list(request):
    recurring_payments = RecurringPayment.objects.filter(
        user=request.user
    ).select_related('category', 'payment_method').order_by('-is_active', '-created_at')

    return render(request, 'app/expenses/recurring_list.html', {
        'recurring_payments': recurring_payments,
    })


@login_required
def create_recurring_payment(request):
    if request.method == 'POST':
        form = RecurringPaymentForm(request.POST, user=request.user)
        if form.is_valid():
            recurring = form.save(commit=False)
            recurring.user = request.user
            recurring.save()
            return redirect('recurring_payment_list')
    else:
        form = RecurringPaymentForm(user=request.user)

    return render(request, 'app/expenses/recurring_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def edit_recurring_payment(request, recurring_id):
    recurring = get_object_or_404(RecurringPayment, id=recurring_id, user=request.user)
    if request.method == 'POST':
        form = RecurringPaymentForm(request.POST, instance=recurring, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('recurring_payment_list')
    else:
        form = RecurringPaymentForm(instance=recurring, user=request.user)

    return render(request, 'app/expenses/recurring_form.html', {
        'form': form,
        'recurring': recurring,
        'is_edit': True,
    })


@login_required
def delete_recurring_payment(request, recurring_id):
    recurring = get_object_or_404(RecurringPayment, id=recurring_id, user=request.user)
    if request.method == 'POST':
        recurring.delete()
    return redirect('recurring_payment_list')


@login_required
def toggle_recurring_payment(request, recurring_id):
    recurring = get_object_or_404(RecurringPayment, id=recurring_id, user=request.user)
    if request.method == 'POST':
        recurring.is_active = not recurring.is_active
        recurring.save(update_fields=['is_active'])
    return redirect('recurring_payment_list')
