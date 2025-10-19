from django.db import models
from django.conf import settings
from datetime import datetime

class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('expense', '支出'),
        ('income', '収入'),
        ('no_change', '変動なし'),
    ]
    MAJOR_CATEGORY_TYPE_CHOICES = [
        ('variable', '変動費'),
        ('fixed', '固定費'),
        ('special', '特別費'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=100)
    major_category = models.CharField(max_length=10, choices=MAJOR_CATEGORY_TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    purpose_description = models.TextField()
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.transaction_type}"



class SensorData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)  # データ保存時に自動的にタイムスタンプを設定
    temperature = models.FloatField()
    humidity = models.FloatField()
    illuminance = models.FloatField(default=None)  # 照度の追加

    def __str__(self):
        return f"{self.timestamp} - Temp: {self.temperature}°C, Humidity: {self.humidity}%, Illuminance: {self.illuminance} lx"
    
class VideoPost(models.Model):
    WIN_LOSS_CHOICES = [
        ('win', '勝ち'),
        ('loss', '負け'),
        ('draw', '引き分け'),
        ('unknown', '不明'),
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
        return f"{self.date} - {self.user.username} - {self.title} - {self.character} - {self.result} - {self.video_url} - {self.notes} - {self.created_at}"
    
    
class Comment(models.Model):
    post = models.ForeignKey(VideoPost, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="コメント内容")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"コメント by {self.user.username} on {self.created_at}"


class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('one_time', '一時'),
        ('recurring', '定期'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', '毎日'),
        ('weekly', '毎週'),
        ('monthly', '毎月'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', '未着手'),
        ('in_progress', '実施中'),
        ('completed', '終了済み'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name="タイトル")
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, verbose_name="タスクタイプ")
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, blank=True, null=True, verbose_name="頻度")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, verbose_name="優先度")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started', verbose_name="ステータス")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="登録日")
    due_date = models.DateTimeField(blank=True, null=True, verbose_name="期限")
    description = models.TextField(blank=True, verbose_name="詳細")

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_date']


class Memo(models.Model):
    MEMO_TYPE_CHOICES = [
        ('note', 'ノート'),
        ('idea', 'アイデア'),
        ('todo', 'TODO'),
        ('reference', '参考資料'),
        ('reminder', 'リマインダー'),
        ('other', 'その他'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memos')
    title = models.CharField(max_length=200, verbose_name="タイトル")
    memo_type = models.CharField(max_length=20, choices=MEMO_TYPE_CHOICES, verbose_name="種別")
    content = models.TextField(verbose_name="詳細")
    is_favorite = models.BooleanField(default=False, verbose_name="お気に入り")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="登録日")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="更新日")

    def __str__(self):
        return f"{self.title} - {self.get_memo_type_display()}"

    class Meta:
        ordering = ['-is_favorite', '-updated_date']


class ShoppingItem(models.Model):
    FREQUENCY_CHOICES = [
        ('one_time', '一時'),
        ('recurring', '定期'),
    ]
    
    STATUS_CHOICES = [
        ('insufficient', '不足'),
        ('available', '残あり'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_items')
    title = models.CharField(max_length=200, verbose_name="タイトル")
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, verbose_name="頻度")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="金額")
    remaining_count = models.IntegerField(default=0, verbose_name="残数")
    threshold_count = models.IntegerField(default=0, verbose_name="不足数")  # 追加: この数以下になると不足とみなす
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='insufficient', verbose_name="ステータス")
    memo = models.TextField(blank=True, verbose_name="メモ")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="登録日")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="更新日")

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # 残数が0未満にならないように制限
        if self.remaining_count < 0:
            self.remaining_count = 0
        
        # 残数と不足数を比較してステータスを自動更新
        if self.remaining_count <= self.threshold_count:
            self.status = 'insufficient'
        else:
            self.status = 'available'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['status', 'remaining_count', '-updated_date']  # 不足を上位に、その後残数が少ない順、更新日順