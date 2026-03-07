from django.db import models
from django.conf import settings


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', '毎日'),
        ('weekly', '毎週'),
        ('monthly', '毎月'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
    )
    title = models.CharField(max_length=100, verbose_name='習慣名')
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='daily',
        verbose_name='頻度',
    )
    # 1〜10 の整数。is_positive で符号を制御する
    coefficient = models.PositiveSmallIntegerField(default=1, verbose_name='係数')
    # True=良い習慣（緑・プラス）、False=悪い習慣（赤・マイナス）
    is_positive = models.BooleanField(default=True, verbose_name='良い習慣')
    # 達成目標（0 は目標なし）
    weekly_goal = models.PositiveSmallIntegerField(default=0, verbose_name='週の目標回数')
    monthly_goal = models.PositiveSmallIntegerField(default=0, verbose_name='月の目標回数')
    is_active = models.BooleanField(default=True, verbose_name='有効')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '習慣'
        verbose_name_plural = '習慣'

    def __str__(self) -> str:
        return self.title

    @property
    def signed_coefficient(self) -> int:
        return self.coefficient if self.is_positive else -self.coefficient

    @property
    def color(self) -> str:
        return '#28a745' if self.is_positive else '#dc3545'


class HabitRecord(models.Model):
    """習慣の達成記録（1日1件、unique_together で重複防止）"""

    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='records')
    date = models.DateField(verbose_name='日付')
    # 達成登録時に上書きした係数（Null の場合は習慣のデフォルト係数を使用）
    coefficient = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='使用係数')
    # 拡張性のため登録日時を記録（画面には表示しない）
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='登録日時')

    class Meta:
        unique_together = ('habit', 'date')
        verbose_name = '習慣記録'
        verbose_name_plural = '習慣記録'

    def __str__(self) -> str:
        return f'{self.habit.title} - {self.date}'

    @property
    def effective_signed_coefficient(self) -> int:
        """実際に使用する signed 係数（記録時上書き値 or 習慣デフォルト）"""
        coeff = self.coefficient if self.coefficient is not None else self.habit.coefficient
        return coeff if self.habit.is_positive else -coeff
