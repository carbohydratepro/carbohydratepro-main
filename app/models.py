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
    
class MajorCategory(models.Model):
    MAJOR_CATEGORY_TYPE_CHOICES = [
        ('fixed', '固定費'),
        ('variable', '変動費'),
        ('special', '特別費'),
    ]
    name = models.CharField(max_length=10, choices=MAJOR_CATEGORY_TYPE_CHOICES)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', '収入'),
        ('expense', '支出'),
        ('no_change', '変動なし'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=100)
    major_category = models.ForeignKey(MajorCategory, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    purpose_description = models.TextField()


# user：取引を行ったユーザー
# amount：金額
# date：取引日
# transaction_type：支出、収入、変動なし
# paymentmethod：支払方法（デフォルトは現金のみ、他はユーザーが登録できて選択式）
# purpose：用途、例（ステーキ）
# major_category：用途の大項目、例（固定費）（固定費、変動費、特別費）
# category：用途の項目、例（食費）（食費、娯楽、病院など、ユーザーが登録できて選択式）
# purpose_description：用途の詳細、例（○○で買った）