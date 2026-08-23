from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.utils import timezone

from app.ordering import move_owned_item, next_sort_order

from .forms import CategoryForm, PaymentMethodForm, RecurringPaymentForm, TransactionForm
from .models import Budget, Category, PaymentMethod, RecurringPayment, Transaction
from . import selectors, services


def _parse_budget_amount(raw: str) -> Decimal | None:
    """予算額の文字列を検証して Decimal を返す。不正なら None。"""
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if amount <= 0 or amount > Decimal('99999999'):
        return None
    return amount


def _selected_ids(request: HttpRequest, name: str) -> list[int]:
    """重複と不正値を除いた複数選択IDを取得する。"""
    selected: list[int] = []
    for raw_value in request.GET.getlist(name):
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            continue
        if value > 0 and value not in selected:
            selected.append(value)
    return selected


def _selected_date(request: HttpRequest) -> str:
    raw_value = request.GET.get('date', '')
    try:
        return date.fromisoformat(raw_value).isoformat() if raw_value else ''
    except ValueError:
        return ''


def _render_expenses_list(
    request: HttpRequest,
    context: dict[str, object],
) -> HttpResponse:
    """グラフ絞り込み時は取引一覧だけを返す。"""
    template_name = (
        'app/expenses/_transaction_list.html'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        else 'app/expenses/list.html'
    )
    return render(request, template_name, context)


@login_required
def budget_view(request: HttpRequest) -> HttpResponse:
    """予算画面。全体・カテゴリ別の月予算を設定し、当月の消化状況を表示する。"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'set_overall':
            amount = _parse_budget_amount(request.POST.get('amount', ''))
            if amount is None:
                messages.error(request, '予算額は1以上の数値で入力してください。')
            else:
                Budget.objects.update_or_create(
                    user=request.user, category=None, defaults={'amount': amount},
                )
                messages.success(request, '全体予算を設定しました。')
            return redirect('budget')

        if action == 'set_category':
            category = get_object_or_404(Category, id=request.POST.get('category_id'), user=request.user)
            amount = _parse_budget_amount(request.POST.get('amount', ''))
            if amount is None:
                messages.error(request, '予算額は1以上の数値で入力してください。')
            else:
                Budget.objects.update_or_create(
                    user=request.user, category=category, defaults={'amount': amount},
                )
                messages.success(request, f'「{category.name}」の予算を設定しました。')
            return redirect('budget')

        if action == 'delete_overall':
            Budget.objects.filter(user=request.user, category=None).delete()
            messages.success(request, '全体予算を解除しました。')
            return redirect('budget')

        if action == 'delete_category':
            category = get_object_or_404(Category, id=request.POST.get('category_id'), user=request.user)
            Budget.objects.filter(user=request.user, category=category).delete()
            messages.success(request, f'「{category.name}」の予算を解除しました。')
            return redirect('budget')

    today = timezone.localdate()
    overview = selectors.build_budget_overview(request.user, today.year, today.month)
    context = {
        'target_month': today.strftime('%Y年%m月'),
        **overview,
    }
    return render(request, 'app/expenses/budget.html', context)


@login_required
def expenses_list(request: HttpRequest) -> HttpResponse:
    from datetime import datetime as dt
    view_mode = request.GET.get('view_mode', 'month')
    target_date_str = request.GET.get('target_date')
    search_query = request.GET.get('search', '')
    per_page_raw = request.GET.get('per_page', '20')
    per_page_options = ['10', '20', '50', '100']
    per_page = int(per_page_raw) if per_page_raw in per_page_options else 20
    sort_by = request.GET.get('sort_by', 'date_desc')

    filter_transaction_type = request.GET.get('transaction_type', '')
    filter_major_category = request.GET.get('major_category', '')
    filter_categories = _selected_ids(request, 'category')
    excluded_categories = _selected_ids(request, 'exclude_category')
    filter_payment_methods = _selected_ids(request, 'payment_method')
    excluded_payment_methods = _selected_ids(request, 'exclude_payment_method')
    filter_date = _selected_date(request)
    filter_category = str(filter_categories[0]) if len(filter_categories) == 1 else ''
    filter_payment_method = str(filter_payment_methods[0]) if len(filter_payment_methods) == 1 else ''

    common_filter_kwargs = {
        'search': search_query,
        'transaction_type': filter_transaction_type,
        'major_category': filter_major_category,
        'category_ids': filter_categories,
        'excluded_category_ids': excluded_categories,
        'payment_method_ids': filter_payment_methods,
        'excluded_payment_method_ids': excluded_payment_methods,
        'exact_date': filter_date,
        'sort_by': sort_by,
    }
    has_active_filters = bool(
        search_query
        or filter_transaction_type
        or filter_major_category
        or filter_categories
        or excluded_categories
        or filter_payment_methods
        or excluded_payment_methods
        or filter_date
    )
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)
    pagination_query = pagination_params.urlencode()

    filter_context = {
        'search_query': search_query,
        'filter_transaction_type': filter_transaction_type,
        'filter_major_category': filter_major_category,
        'filter_category': filter_category,
        'filter_payment_method': filter_payment_method,
        'filter_categories': filter_categories,
        'excluded_categories': excluded_categories,
        'filter_payment_methods': filter_payment_methods,
        'excluded_payment_methods': excluded_payment_methods,
        'filter_date': filter_date,
        'has_active_filters': has_active_filters,
        'pagination_query': pagination_query,
    }

    if view_mode == 'year':
        start_date, end_date, current_year = selectors.get_year_date_range(target_date_str)
        transactions_qs = selectors.get_transactions(request.user, start_date, end_date, **common_filter_kwargs)
        transactions_count = transactions_qs.count()
        paginator = Paginator(transactions_qs, per_page)
        transactions_page = paginator.get_page(request.GET.get('page'))
        summary = selectors.get_summary(transactions_qs)
        monthly_chart_data_json = selectors.build_monthly_chart_data(transactions_qs, current_year)
        current_month_str = dt.now().strftime('%Y-%m')
        year_range = list(range(current_year - 5, current_year + 3))

        return _render_expenses_list(request, {
            'view_mode': 'year',
            'current_year': current_year,
            'year_range': year_range,
            'monthly_chart_data_json': monthly_chart_data_json,
            'transactions_page': transactions_page,
            'transactions_count': transactions_count,
            'total_income': summary['total_income'],
            'total_expense': summary['total_expense'],
            'net_balance': summary['net_balance'],
            'total_income_formatted': '{:,.0f}'.format(float(summary['total_income'])),
            'total_expense_formatted': '{:,.0f}'.format(float(summary['total_expense'])),
            'net_balance_formatted': '{:,.0f}'.format(float(summary['net_balance'])),
            'target_month': f'{current_year}年',
            'user_categories': selectors.get_categories(request.user),
            'user_payment_methods': selectors.get_payment_methods(request.user),
            'default_target_date': str(current_year),
            'per_page': per_page,
            'per_page_options': per_page_options,
            'sort_by': sort_by,
            'year_for_toggle': current_year,
            'month_for_toggle': current_month_str,
            **filter_context,
        })

    # 月表示モード
    start_date, end_date, date_range = selectors.get_date_range(target_date_str)
    transactions_qs = selectors.get_transactions(request.user, start_date, end_date, **common_filter_kwargs)
    transactions_count = transactions_qs.count()
    paginator = Paginator(transactions_qs, per_page)
    transactions_page = paginator.get_page(request.GET.get('page'))
    summary = selectors.get_summary(transactions_qs)

    category_data_json = selectors.build_category_chart_data(transactions_qs)
    major_category_data_json = selectors.build_major_category_chart_data(transactions_qs)
    expense_data_json, balance_data_json = selectors.build_daily_chart_data(transactions_qs, date_range)

    return _render_expenses_list(request, {
        'view_mode': 'month',
        'transactions_page': transactions_page,
        'transactions_count': transactions_count,
        'category_data_json': category_data_json,
        'major_category_data_json': major_category_data_json,
        'expense_data_json': expense_data_json,
        'balance_data_json': balance_data_json,
        'total_income': summary['total_income'],
        'total_expense': summary['total_expense'],
        'net_balance': summary['net_balance'],
        'total_income_formatted': '{:,.0f}'.format(float(summary['total_income'])),
        'total_expense_formatted': '{:,.0f}'.format(float(summary['total_expense'])),
        'net_balance_formatted': '{:,.0f}'.format(float(summary['net_balance'])),
        'target_month': start_date.strftime('%Y年%m月'),
        'user_categories': selectors.get_categories(request.user),
        'user_payment_methods': selectors.get_payment_methods(request.user),
        'default_target_date': start_date.strftime('%Y-%m'),
        'per_page': per_page,
        'per_page_options': per_page_options,
        'sort_by': sort_by,
        'year_for_toggle': start_date.year,
        'month_for_toggle': start_date.strftime('%Y-%m'),
        **filter_context,
    })


@login_required
def create_expenses(request: HttpRequest) -> HttpResponse:
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
def expenses_settings(request: HttpRequest) -> HttpResponse:
    payments = selectors.get_payment_methods(request.user)
    # 各カテゴリに実効グラフ色（設定色 or ID由来の既定色）を付与してテンプレートへ渡す
    purposes = list(selectors.get_categories(request.user))
    for purpose in purposes:
        purpose.effective_chart_color = selectors.get_effective_category_color(purpose)

    payment_form = PaymentMethodForm(prefix='payment')
    purpose_form = CategoryForm(prefix='purpose')

    edit_payment_instance = None
    edit_purpose_instance = None

    if request.method == 'POST':
        if 'payment_id' in request.POST:
            payment = get_object_or_404(PaymentMethod, id=request.POST.get('payment_id'), user=request.user)
            if 'move_payment' in request.POST:
                move_owned_item(
                    PaymentMethod,
                    request.user,
                    payment.pk,
                    request.POST.get('direction', ''),
                )
                return redirect('expenses_settings')
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
            if 'move_purpose' in request.POST:
                move_owned_item(
                    Category,
                    request.user,
                    purpose.pk,
                    request.POST.get('direction', ''),
                )
                return redirect('expenses_settings')
            if 'edit_purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, instance=purpose, prefix='purpose')
                if purpose_form.is_valid():
                    updated = purpose_form.save(commit=False)
                    # 「自動で色分け」チェック時は色を未設定に戻す（IDに応じた既定色を使う）
                    if request.POST.get('purpose-auto_color'):
                        updated.chart_color = ''
                    updated.save()
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
                    new_payment.sort_order = next_sort_order(PaymentMethod, request.user)
                    new_payment.save()
                    return redirect('expenses_settings')

            elif 'purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, prefix='purpose')
                if services.is_category_limit_reached(request.user):
                    purpose_form.add_error(None, f'使用用途の登録上限数は{services.CATEGORY_LIMIT}件です。')
                elif purpose_form.is_valid():
                    new_purpose = purpose_form.save(commit=False)
                    new_purpose.user = request.user
                    new_purpose.sort_order = next_sort_order(Category, request.user)
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
def edit_expenses(request: HttpRequest, transaction_id: int) -> HttpResponse:
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
def delete_expenses(request: HttpRequest, transaction_id: int) -> HttpResponse:
    from ..deletion import archive_and_delete

    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        archive_and_delete(transaction, request.user)
        messages.success(request, '取引を削除しました。ごみ箱から元に戻せます。')
    return redirect('expense_list')


@login_required
def bulk_delete_expenses(request: HttpRequest) -> JsonResponse:
    """取引の一括削除（選択モード用）"""
    from ..bulk_delete import bulk_delete_response
    return bulk_delete_response(request, Transaction)


@login_required
def recurring_payment_list(request: HttpRequest) -> HttpResponse:
    return render(request, 'app/expenses/recurring_list.html', {
        'recurring_payments': selectors.get_recurring_payments(request.user),
    })


@login_required
def create_recurring_payment(request: HttpRequest) -> HttpResponse:
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
def edit_recurring_payment(request: HttpRequest, recurring_id: int) -> HttpResponse:
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
def delete_recurring_payment(request: HttpRequest, recurring_id: int) -> HttpResponse:
    from ..deletion import archive_and_delete

    recurring = get_object_or_404(RecurringPayment, id=recurring_id, user=request.user)
    if request.method == 'POST':
        archive_and_delete(recurring, request.user)
        messages.success(request, '定期支払いを削除しました。ごみ箱から元に戻せます。')
    return redirect('recurring_payment_list')


@login_required
def toggle_recurring_payment(request: HttpRequest, recurring_id: int) -> HttpResponse:
    recurring = get_object_or_404(RecurringPayment, id=recurring_id, user=request.user)
    if request.method == 'POST':
        recurring.is_active = not recurring.is_active
        recurring.save(update_fields=['is_active'])
    return redirect('recurring_payment_list')
