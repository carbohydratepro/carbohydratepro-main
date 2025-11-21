from django.db import models
from django.conf import settings


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
