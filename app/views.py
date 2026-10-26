from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.http import urlencode
from zoneinfo import ZoneInfo
from .forms import ContactMessageForm
from .models import ContactMessage
import logging

logger = logging.getLogger(__name__)

from .expenses.views import (
    expenses_list, create_expenses, expenses_settings, edit_expenses, delete_expenses,
    bulk_delete_expenses, budget_view,
    recurring_payment_list, create_recurring_payment, edit_recurring_payment,
    delete_recurring_payment, toggle_recurring_payment,
)
from .memo.views import memo_list, create_memo, edit_memo, delete_memo, bulk_delete_memos, toggle_memo_favorite, memo_settings
from .shopping.views import shopping_list, create_shopping_item, edit_shopping_item, delete_shopping_item, bulk_delete_shopping_items, update_shopping_count, toggle_check_shopping_item, clear_checked_shopping_items
from .task.views import (
    task_list, create_task, edit_task, delete_task, get_day_tasks, task_settings,
    temp_task_board, temp_task_api, temp_task_detail_api, temp_task_clear_api,
    temp_task_sets_api, temp_task_set_detail_api,
)
from .habit.views import habit_dashboard, create_habit, edit_habit, delete_habit, toggle_habit, habit_status_json, habit_heatmap_json, habit_list
from .home_views import dashboard
from .trash_views import restore_deleted_item, trash
from .cooking.views import (
    cooking_create,
    cooking_delete,
    cooking_detail,
    cooking_edit,
    cooking_history_add,
    cooking_history_delete,
    cooking_history_update,
    cooking_list,
    cooking_record_today,
)
from .manage_views import manage_dashboard, manage_contacts, manage_contact_update, manage_users, manage_users_stats_api, manage_analytics, manage_analytics_api

CONTACT_HISTORY_PER_PAGE = 10


@login_required
def contact(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            contact_message.user = request.user
            contact_message.save()
            
            try:
                inquiry_type_display = contact_message.get_inquiry_type_display()
                subject = f"【お問い合わせ】{inquiry_type_display}: {contact_message.subject}"
                sent_at = timezone.localtime(contact_message.created_at, ZoneInfo("Asia/Tokyo"))
                message = f"""
新しいお問い合わせが届きました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【お問い合わせ情報】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

種類: {inquiry_type_display}
件名: {contact_message.subject}
送信者: {request.user.email}
送信日時: {sent_at.strftime('%Y年%m月%d日 %H:%M:%S')}（日本時間）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【お問い合わせ内容】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{contact_message.message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

このメールは自動送信されています。
お問い合わせへの対応が完了したら、管理画面で「対応済み」にマークしてください。
"""
                admin_email = getattr(settings, "SECURITY_ALERT_EMAIL", "carbohydratepro@gmail.com")
                send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[admin_email], fail_silently=False)
                messages.success(request, "お問い合わせを送信しました。ご連絡ありがとうございます。")
                logger.info(f"お問い合わせメール送信成功: {request.user.email} - {inquiry_type_display}")
            except Exception as e:
                logger.error(f"お問い合わせメール送信エラー: {str(e)}")
                messages.warning(request, "お問い合わせは保存されましたが、メール送信に失敗しました。")
            
            return redirect("contact")
        else:
            messages.error(request, "フォームに入力エラーがあります。")
    else:
        form = ContactMessageForm()
    
    search_query = request.GET.get("q", "").strip()
    inquiry_filter = request.GET.get("inquiry_type", "")
    if inquiry_filter not in dict(ContactMessage.INQUIRY_TYPE_CHOICES):
        inquiry_filter = ""

    user_messages = ContactMessage.objects.filter(user=request.user)
    has_any_history = user_messages.exists()
    if search_query:
        user_messages = user_messages.filter(Q(subject__icontains=search_query) | Q(message__icontains=search_query))
    if inquiry_filter:
        user_messages = user_messages.filter(inquiry_type=inquiry_filter)

    page_obj = Paginator(user_messages, CONTACT_HISTORY_PER_PAGE).get_page(request.GET.get("page"))
    filter_params = {key: value for key, value in (("q", search_query), ("inquiry_type", inquiry_filter)) if value}

    context = {
        "form": form,
        "page_obj": page_obj,
        "user_messages": page_obj.object_list,
        "has_any_history": has_any_history,
        "search_query": search_query,
        "inquiry_filter": inquiry_filter,
        "inquiry_choices": ContactMessage.INQUIRY_TYPE_CHOICES,
        "filter_querystring": urlencode(filter_params),
    }
    return render(request, "app/contact.html", context)


@login_required
def contact_detail(request: HttpRequest, contact_id: int) -> HttpResponse:
    """自分が送信したお問い合わせの全文と返信を表示する。"""
    contact_message = get_object_or_404(ContactMessage, id=contact_id, user=request.user)
    return render(request, "app/contact_detail.html", {"contact_message": contact_message})
