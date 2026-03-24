from django.db import models
from django.conf import settings

from .expenses.models import PaymentMethod, Category, Transaction
from .memo.models import Memo
from .shopping.models import ShoppingItem
from .task.models import TaskLabel, Task
from .habit.models import Habit, HabitRecord

class ContactMessage(models.Model):
    INQUIRY_TYPE_CHOICES = [
        ("bug", "バグ報告"),
        ("feature", "機能要望"),
        ("question", "質問"),
        ("other", "その他"),
    ]

    STATUS_CHOICES = [
        ("open", "未対応"),
        ("in_progress", "対応中"),
        ("resolved", "対応済み"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_messages")
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, verbose_name="お問い合わせの種類")
    subject = models.CharField(max_length=200, verbose_name="件名")
    message = models.TextField(verbose_name="お問い合わせ内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="送信日時")
    is_resolved = models.BooleanField(default=False, verbose_name="対応済み")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open", verbose_name="ステータス")
    admin_reply = models.TextField(blank=True, verbose_name="管理者返信")
    admin_reply_at = models.DateTimeField(null=True, blank=True, verbose_name="返信日時")
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "お問い合わせ"
        verbose_name_plural = "お問い合わせ"
    
    def __str__(self) -> str:
        return f"{self.get_inquiry_type_display()} - {self.subject} ({self.user.email})"

