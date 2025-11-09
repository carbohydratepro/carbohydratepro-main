from django.db import models
from django.conf import settings
from datetime import datetime


class ContactMessage(models.Model):
    """お問い合わせメッセージモデル"""
    INQUIRY_TYPE_CHOICES = [
        ('bug', 'バグ報告'),
        ('feature', '機能要望'),
        ('question', '質問'),
        ('other', 'その他'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contact_messages')
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, verbose_name='お問い合わせの種類')
    subject = models.CharField(max_length=200, verbose_name='件名')
    message = models.TextField(verbose_name='お問い合わせ内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='送信日時')
    is_resolved = models.BooleanField(default=False, verbose_name='対応済み')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'お問い合わせ'
        verbose_name_plural = 'お問い合わせ'
    
    def __str__(self):
        return f"{self.get_inquiry_type_display()} - {self.subject} ({self.user.email})"


class TaskLabel(models.Model):
    """タスクラベルモデル"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_labels')
    name = models.CharField(max_length=30, verbose_name="ラベル名")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="色")  # HEXカラーコード
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'タスクラベル'
        verbose_name_plural = 'タスクラベル'


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


class TaskLabel(models.Model):
    """タスクラベルモデル"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_labels')
    name = models.CharField(max_length=30, verbose_name="ラベル名")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="色")  # HEXカラーコード
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'タスクラベル'
        verbose_name_plural = 'タスクラベル'


class Task(models.Model):
    FREQUENCY_CHOICES = [
        ('', '---'),
        ('daily', '毎日'),
        ('weekly', '毎週'),
        ('monthly', '毎月'),
        ('yearly', '毎年'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', '未着手'),
        ('in_progress', '実施中'),
        ('completed', '完了'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name="タイトル")
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, blank=True, default='', verbose_name="頻度")
    repeat_interval = models.IntegerField(default=1, verbose_name="繰り返し間隔")  # 例: 2なら「2週ごと」
    repeat_count = models.IntegerField(blank=True, null=True, verbose_name="繰り返し回数")  # 何回繰り返すか（Noneなら無制限）
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="優先度")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started', verbose_name="ステータス")
    label = models.ForeignKey('TaskLabel', on_delete=models.SET_NULL, blank=True, null=True, related_name='tasks', verbose_name="ラベル")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="登録日")
    start_date = models.DateTimeField(blank=True, null=True, verbose_name="開始日時")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="終了日時")
    all_day = models.BooleanField(default=False, verbose_name="終日")
    description = models.TextField(blank=True, verbose_name="詳細")
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='recurring_instances', verbose_name="親タスク")

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
        # 残数を0～999の範囲に制限
        if self.remaining_count < 0:
            self.remaining_count = 0
        elif self.remaining_count > 999:
            self.remaining_count = 999
        
        # 不足数を0～999の範囲に制限
        if self.threshold_count < 0:
            self.threshold_count = 0
        elif self.threshold_count > 999:
            self.threshold_count = 999
        
        # 残数と不足数を比較してステータスを自動更新
        if self.remaining_count <= self.threshold_count:
            self.status = 'insufficient'
        else:
            self.status = 'available'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['status', 'remaining_count', '-updated_date']  # 不足を上位に、その後残数が少ない順、更新日順