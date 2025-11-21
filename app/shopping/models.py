from django.db import models
from django.conf import settings


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
