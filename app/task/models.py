from django.db import models
from django.conf import settings


class TaskLabel(models.Model):
    """タスクラベルモデル"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_labels')
    name = models.CharField(max_length=30, verbose_name="ラベル名")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="色")  # HEXカラーコード
    
    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_date']
