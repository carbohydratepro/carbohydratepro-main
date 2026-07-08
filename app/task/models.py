import uuid

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


class TempTaskSet(models.Model):
    """一時タスクセット（グループ）モデル"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='temp_task_sets')
    name = models.CharField(max_length=50, verbose_name="セット名")
    order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = '一時タスクセット'
        verbose_name_plural = '一時タスクセット'


class TempTaskItem(models.Model):
    """一時タスク（サーバー永続化）モデル"""
    STATUS_CHOICES = [
        ('todo', 'やること'),
        ('doing', 'やってる'),
        ('done', 'できた'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='temp_task_items')
    task_set = models.ForeignKey(TempTaskSet, on_delete=models.CASCADE, null=True, blank=True, related_name='items', verbose_name="セット")
    title = models.CharField(max_length=200, verbose_name="タイトル")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo', verbose_name="ステータス")
    order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = '一時タスク'
        verbose_name_plural = '一時タスク'


class CalendarToken(models.Model):
    """ICSカレンダー配信用のユーザー別トークン。

    URLを知っている人だけが購読できるcapability方式。
    漏えい時は再生成で旧URLを無効化する。
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_token',
        verbose_name='ユーザー',
    )
    token = models.UUIDField('トークン', default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = 'カレンダー配信トークン'
        verbose_name_plural = 'カレンダー配信トークン'

    def __str__(self) -> str:
        return f'{self.user} のカレンダートークン'

    def regenerate(self) -> None:
        """トークンを再生成して旧URLを無効化する。"""
        self.token = uuid.uuid4()
        self.save(update_fields=['token'])


class ExternalCalendar(models.Model):
    """外部カレンダーの購読設定（ICS URLの取り込み）。

    Google カレンダーの「非公開のiCal URL」等を登録し、
    cron の sync_external_calendars で定期的に取り込む。読み取り専用。
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='external_calendars',
        verbose_name='ユーザー',
    )
    name = models.CharField('カレンダー名', max_length=100)
    url = models.URLField('ICS URL', max_length=500)
    color = models.CharField('色', max_length=7, default='#6c8ebf')
    last_synced_at = models.DateTimeField('最終同期日時', null=True, blank=True)
    last_error = models.CharField('最終同期エラー', max_length=200, blank=True, default='')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'url'], name='unique_external_calendar_url_per_user'),
        ]
        verbose_name = '外部カレンダー'
        verbose_name_plural = '外部カレンダー'

    def __str__(self) -> str:
        return f'{self.user} の外部カレンダー: {self.name}'


class ExternalEvent(models.Model):
    """外部カレンダーから取り込んだイベント（読み取り専用）。

    同期のたびに購読範囲内のイベントを洗い替えする。
    テンプレートで Task と混在表示できるよう、start_date / end_date /
    all_day / label（=カレンダー）等の互換プロパティを持つ。
    """
    calendar = models.ForeignKey(
        ExternalCalendar,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='外部カレンダー',
    )
    uid = models.CharField('UID', max_length=500, blank=True, default='')
    title = models.CharField('タイトル', max_length=300)
    start_date = models.DateTimeField('開始日時')
    end_date = models.DateTimeField('終了日時', null=True, blank=True)
    all_day = models.BooleanField('終日', default=False)

    # Task と混在表示するときのテンプレート互換用
    status = ''

    class Meta:
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['calendar', 'start_date']),
        ]
        verbose_name = '外部イベント'
        verbose_name_plural = '外部イベント'

    def __str__(self) -> str:
        return f'{self.title}（{self.calendar.name}）'

    @property
    def is_external(self) -> bool:
        return True

    @property
    def label(self) -> ExternalCalendar:
        """カレンダーをラベル互換（.name / .color）として返す。"""
        return self.calendar
