from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, PaymentMethodForm, RecurringPaymentForm, TransactionForm
from .models import Category, PaymentMethod, RecurringPayment, Transaction
from . import selectors, services


@login_required
def expenses_list(request):
    target_date_str = request.GET.get('target_date')
    search_query = request.GET.get('search', '')
    per_page_raw = request.GET.get('per_page', '20')
    per_page_options = ['10', '20', '50', '100']
    per_page = int(per_page_raw) if per_page_raw in per_page_options else 20

    filter_transaction_type = request.GET.get('transaction_type', '')
    filter_major_category = request.GET.get('major_category', '')
    filter_category = request.GET.get('category', '')
    filter_payment_method = request.GET.get('payment_method', '')

    start_date, end_date, date_range = selectors.get_date_range(target_date_str)

    transactions_qs = selectors.get_transactions(
        request.user,
        start_date,
        end_date,
        search=search_query,
        transaction_type=filter_transaction_type,
        major_category=filter_major_category,
        category_id=filter_category,
        payment_method_id=filter_payment_method,
    )

    transactions_count = transactions_qs.count()
    paginator = Paginator(transactions_qs, per_page)
    transactions_page = paginator.get_page(request.GET.get('page'))

    summary = selectors.get_summary(transactions_qs)
    total_income = summary['total_income']
    total_expense = summary['total_expense']
    net_balance = summary['net_balance']

    category_data_json = selectors.build_category_chart_data(transactions_qs)
    major_category_data_json = selectors.build_major_category_chart_data(transactions_qs)
    expense_data_json, balance_data_json = selectors.build_daily_chart_data(transactions_qs, date_range)

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
        'total_income_formatted': '{:,.0f}'.format(float(total_income)),
        'total_expense_formatted': '{:,.0f}'.format(float(total_expense)),
        'net_balance_formatted': '{:,.0f}'.format(float(net_balance)),
        'target_month': start_date.strftime('%Y年%m月'),
        'search_query': search_query,
        'user_categories': selectors.get_categories(request.user),
        'user_payment_methods': selectors.get_payment_methods(request.user),
        'filter_transaction_type': filter_transaction_type,
        'filter_major_category': filter_major_category,
        'filter_category': filter_category,
        'filter_payment_method': filter_payment_method,
        'default_target_date': start_date.strftime('%Y-%m'),
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
    payments = selectors.get_payment_methods(request.user)
    purposes = selectors.get_categories(request.user)

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
                if services.is_payment_method_limit_reached(request.user):
                    payment_form.add_error(None, f'支払方法の登録上限数は{services.PAYMENT_METHOD_LIMIT}件です。')
                elif payment_form.is_valid():
                    new_payment = payment_form.save(commit=False)
                    new_payment.user = request.user
                    new_payment.save()
                    return redirect('expenses_settings')

            elif 'purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, prefix='purpose')
                if services.is_category_limit_reached(request.user):
                    purpose_form.add_error(None, f'使用用途の登録上限数は{services.CATEGORY_LIMIT}件です。')
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


@login_required
def recurring_payment_list(request):
    return render(request, 'app/expenses/recurring_list.html', {
        'recurring_payments': selectors.get_recurring_payments(request.user),
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
