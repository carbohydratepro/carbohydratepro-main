from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactMessageForm
from .models import ContactMessage
import logging

logger = logging.getLogger(__name__)

from .expenses.views import (
    expenses_list, create_expenses, expenses_settings, edit_expenses, delete_expenses,
    recurring_payment_list, create_recurring_payment, edit_recurring_payment,
    delete_recurring_payment, toggle_recurring_payment, execute_recurring_payments,
)
from .memo.views import memo_list, create_memo, edit_memo, delete_memo, toggle_memo_favorite, memo_settings
from .shopping.views import shopping_list, create_shopping_item, edit_shopping_item, delete_shopping_item, update_shopping_count
from .task.views import task_list, create_task, edit_task, delete_task, get_day_tasks, task_settings

@login_required
def contact(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            contact_message.user = request.user
            contact_message.save()
            
            try:
                inquiry_type_display = contact_message.get_inquiry_type_display()
                subject = f"【お問い合わせ】{inquiry_type_display}: {contact_message.subject}"
                message = f"""
新しいお問い合わせが届きました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【お問い合わせ情報】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

種類: {inquiry_type_display}
件名: {contact_message.subject}
送信者: {request.user.email}
送信日時: {contact_message.created_at.strftime('%Y年%m月%d日 %H:%M:%S')}

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
    
    user_messages = ContactMessage.objects.filter(user=request.user)[:10]
    context = {"form": form, "user_messages": user_messages}
    return render(request, "app/contact.html", context)
