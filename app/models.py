from django.db import models
from django.conf import settings

from .expenses.models import PaymentMethod, Category, Transaction
from .memo.models import Memo
from .shopping.models import ShoppingItem
from .task.models import TaskLabel, Task

class ContactMessage(models.Model):
    INQUIRY_TYPE_CHOICES = [
        ("bug", "バグ報告"),
        ("feature", "機能要望"),
        ("question", "質問"),
        ("other", "その他"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_messages")
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, verbose_name="お問い合わせの種類")
    subject = models.CharField(max_length=200, verbose_name="件名")
    message = models.TextField(verbose_name="お問い合わせ内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="送信日時")
    is_resolved = models.BooleanField(default=False, verbose_name="対応済み")
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "お問い合わせ"
        verbose_name_plural = "お問い合わせ"
    
    def __str__(self):
        return f"{self.get_inquiry_type_display()} - {self.subject} ({self.user.email})"

