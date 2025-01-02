from django.db import models
from django.conf import settings

class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    
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
    timestamp = models.DateTimeField()  
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
    ]

    date = models.DateField(verbose_name="年月日")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="video_posts")
    result = models.CharField(max_length=10, choices=WIN_LOSS_CHOICES, verbose_name="勝敗")
    video_url = models.URLField(verbose_name="動画URL")
    notes = models.TextField(blank=True, verbose_name="補足")

    def __str__(self):
        return f"{self.date} - {self.user.username} - {self.result}"
    
    
class Comment(models.Model):
    post = models.ForeignKey(VideoPost, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="コメント内容")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"コメント by {self.user.username} on {self.created_at}"