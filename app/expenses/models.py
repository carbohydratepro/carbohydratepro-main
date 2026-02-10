from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxLengthValidator


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
    
    def __str__(self) -> str:
        return f"{self.user.email} - {self.amount} - {self.transaction_type}"


class RecurringPayment(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', '毎日'),
        ('weekly', '毎週'),
        ('monthly', '毎月'),
        ('yearly', '毎年'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recurring_payments',
    )
    purpose = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10,
        choices=Transaction.TRANSACTION_TYPE_CHOICES,
        default='expense',
    )
    major_category = models.CharField(
        max_length=10,
        choices=Transaction.MAJOR_CATEGORY_TYPE_CHOICES,
        default='fixed',
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    purpose_description = models.TextField(blank=True, default='')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    days_of_week = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
        validators=[MaxLengthValidator(7)],
        help_text='曜日リスト（0=月曜, 6=日曜）。毎週の場合に使用。最大7つ。',
    )
    days_of_month = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
        validators=[MaxLengthValidator(7)],
        help_text='日リスト（1-31）。毎月・毎年の場合に使用。最大7つ。',
    )
    month_of_year = models.IntegerField(
        null=True,
        blank=True,
        help_text='月（1-12）。毎年の場合に使用。',
    )
    is_active = models.BooleanField(default=True)
    last_executed = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.purpose} - {self.get_frequency_display()}"

    def should_execute_on(self, target_date: 'date') -> bool:
        """指定日に実行すべきかどうかを判定する"""
        from datetime import date  # noqa: F811

        if not self.is_active:
            return False

        if self.last_executed and self.last_executed >= target_date:
            return False

        if self.frequency == 'daily':
            return True
        elif self.frequency == 'weekly':
            # 曜日リストのいずれかに一致すれば実行
            days = self.days_of_week if self.days_of_week else [0]
            return target_date.weekday() in days
        elif self.frequency == 'monthly':
            # 日リストのいずれかに一致すれば実行（月末調整あり）
            import calendar
            days = self.days_of_month if self.days_of_month else [1]
            last_day = calendar.monthrange(target_date.year, target_date.month)[1]
            effective_days = [min(d, last_day) for d in days]
            return target_date.day in effective_days
        elif self.frequency == 'yearly':
            # 指定月かつ日リストのいずれかに一致すれば実行
            import calendar
            month = self.month_of_year or 1
            if target_date.month != month:
                return False
            days = self.days_of_month if self.days_of_month else [1]
            last_day = calendar.monthrange(target_date.year, target_date.month)[1]
            effective_days = [min(d, last_day) for d in days]
            return target_date.day in effective_days

        return False

    def execute(self, target_date: 'date') -> 'Transaction':
        """定期支払いを実行し、Transactionを作成する"""
        from django.utils.timezone import make_aware
        from datetime import datetime

        transaction = Transaction.objects.create(
            user=self.user,
            amount=self.amount,
            date=make_aware(datetime.combine(target_date, datetime.min.time())),
            transaction_type=self.transaction_type,
            payment_method=self.payment_method,
            purpose=self.purpose,
            major_category=self.major_category,
            category=self.category,
            purpose_description=self.purpose_description or f'定期支払い（{self.get_frequency_display()}）',
        )
        self.last_executed = target_date
        self.save(update_fields=['last_executed'])
        return transaction
