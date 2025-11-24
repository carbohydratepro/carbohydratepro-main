from django.db import models
from django.conf import settings


class MemoType(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memo_types', null=True, blank=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6c757d')

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Memo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memos')
    title = models.CharField(max_length=200, verbose_name="タイトル")
    memo_type = models.ForeignKey(MemoType, on_delete=models.PROTECT, related_name='memos', verbose_name="種別")
    content = models.TextField(verbose_name="詳細", blank=True)
    is_favorite = models.BooleanField(default=False, verbose_name="お気に入り")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="登録日")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="更新日")

    def __str__(self):
        return f"{self.title} - {self.memo_type.name}"

    class Meta:
        ordering = ['-is_favorite', '-updated_date']
