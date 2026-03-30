from django.db import models
from django.conf import settings

from .expenses.models import PaymentMethod, Category, Transaction
from .memo.models import Memo
from .shopping.models import ShoppingItem
from .task.models import TaskLabel, Task
from .habit.models import Habit, HabitRecord


class ActivityLog(models.Model):
    """各画面へのアクセスと操作（追加・編集・削除等）を記録するモデル"""

    PAGE_CHOICES = [
        ("expenses", "家計簿"),
        ("tasks", "タスク"),
        ("memos", "メモ"),
        ("shopping", "買うものリスト"),
        ("habits", "習慣トラッカー"),
        ("demo", "デモ"),
    ]

    ACTION_CHOICES = [
        ("view", "閲覧"),
        ("create", "追加"),
        ("edit", "編集"),
        ("delete", "削除"),
        ("toggle", "切替"),
    ]

    page = models.CharField(max_length=20, choices=PAGE_CHOICES, verbose_name="機能")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="操作")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ユーザー",
    )
    accessed_at = models.DateTimeField(auto_now_add=True, verbose_name="日時")

    class Meta:
        ordering = ["-accessed_at"]
        verbose_name = "アクティビティログ"
        verbose_name_plural = "アクティビティログ"
        indexes = [
            models.Index(fields=["page", "action", "accessed_at"]),
        ]

    def __str__(self) -> str:
        username = self.user.username if self.user else "不明"
        return f"{self.get_page_display()} / {self.get_action_display()} - {username} ({self.accessed_at})"


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

