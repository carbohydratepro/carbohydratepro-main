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

class SensorData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    illuminance = models.FloatField(default=None)

    def __str__(self):
        return f"{self.timestamp} - Temp: {self.temperature}°C, Humidity: {self.humidity}%, Illuminance: {self.illuminance} lx"

class VideoPost(models.Model):
    WIN_LOSS_CHOICES = [
        ("win", "勝ち"),
        ("loss", "負け"),
        ("draw", "引き分け"),
        ("unknown", "不明"),
    ]

    date = models.DateField(verbose_name="年月日")
    title = models.CharField(max_length=200, default="新しい動画", verbose_name="タイトル")
    character = models.CharField(max_length=30, default="不明", verbose_name="使用キャラ")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ユーザー")
    result = models.CharField(max_length=10, choices=WIN_LOSS_CHOICES, verbose_name="勝敗")
    video_url = models.URLField(verbose_name="動画URL")
    notes = models.TextField(blank=True, verbose_name="詳細")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.user.username} - {self.title}"

class Comment(models.Model):
    post = models.ForeignKey(VideoPost, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="コメント内容")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"コメント by {self.user.username} on {self.created_at}"