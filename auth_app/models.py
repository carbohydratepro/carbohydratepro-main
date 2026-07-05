from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta


AVATAR_MAX_SIZE = 2 * 1024 * 1024
AVATAR_ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
AVATAR_ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}


def validate_avatar_file(file: object) -> None:
    """アカウントアイコン用画像を検証する。"""
    max_size = getattr(settings, 'ACCOUNT_AVATAR_MAX_SIZE', AVATAR_MAX_SIZE)
    if getattr(file, 'size', 0) > max_size:
        raise ValidationError('アカウントアイコンは2MB以下の画像を選択してください。')

    extension = Path(getattr(file, 'name', '')).suffix.lower()
    if extension not in AVATAR_ALLOWED_EXTENSIONS:
        raise ValidationError('アカウントアイコンはJPEG、PNG、WebP形式のみ利用できます。')

    content_type = getattr(file, 'content_type', '')
    if content_type and content_type not in AVATAR_ALLOWED_CONTENT_TYPES:
        raise ValidationError('アカウントアイコンはJPEG、PNG、WebP形式のみ利用できます。')

    position = file.tell() if hasattr(file, 'tell') else None
    header = file.read(16) if hasattr(file, 'read') else b''
    if position is not None and hasattr(file, 'seek'):
        file.seek(position)

    is_jpeg = header.startswith(b'\xff\xd8\xff')
    is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
    is_webp = len(header) >= 12 and header[:4] == b'RIFF' and header[8:12] == b'WEBP'
    if header and not (is_jpeg or is_png or is_webp):
        raise ValidationError('アカウントアイコンの画像形式を確認できません。')

class CustomUserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> 'CustomUser':
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: object) -> 'CustomUser':
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, default=None)
    avatar = models.FileField(
        'アカウントアイコン',
        upload_to='account_avatars/',
        blank=True,
        validators=[validate_avatar_file],
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # 追加フィールド
    created_at = models.DateTimeField('作成日時', auto_now_add=True, null=True)
    last_login_at = models.DateTimeField('最終ログイン日時', null=True, blank=True)
    last_active_at = models.DateTimeField('最終アクティブ日時', null=True, blank=True)
    login_attempt_count = models.IntegerField('ログイン試行回数', default=0)
    access_count = models.IntegerField('アクセス数', default=0)
    
    # メールアドレス認証済みフラグ
    is_email_verified = models.BooleanField('メールアドレス認証済み', default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self) -> str:
        return self.email or "未指定ユーザー"


class AccountGroup(models.Model):
    """相互に切替可能なアカウント群。"""
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = 'アカウントグループ'
        verbose_name_plural = 'アカウントグループ'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'AccountGroup #{self.pk}'


class AccountMembership(models.Model):
    """アカウントグループへのユーザー所属。"""
    group = models.ForeignKey(
        AccountGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='アカウントグループ',
    )
    user = models.OneToOneField(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='account_membership',
        verbose_name='ユーザー',
    )
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_account_memberships',
        verbose_name='追加したユーザー',
    )
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = 'アカウント所属'
        verbose_name_plural = 'アカウント所属'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'{self.user.email} in {self.group_id}'


class AccountGroupLink(models.Model):
    """アカウントグループ間の親子関係。

    親グループとその直接の子グループが1つの「ファミリー」を構成し、
    ファミリー内のアカウントは相互に切替できる。
    子グループは複数の親を持てるが、孫（子の子）や子の別の親は辿らない。
    """
    parent = models.ForeignKey(
        AccountGroup,
        on_delete=models.CASCADE,
        related_name='child_links',
        verbose_name='親グループ',
    )
    child = models.ForeignKey(
        AccountGroup,
        on_delete=models.CASCADE,
        related_name='parent_links',
        verbose_name='子グループ',
    )
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_account_group_links',
        verbose_name='作成したユーザー',
    )
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = 'アカウントグループ連携'
        verbose_name_plural = 'アカウントグループ連携'
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(fields=['parent', 'child'], name='unique_account_group_link'),
            models.CheckConstraint(check=~models.Q(parent=models.F('child')), name='account_group_link_not_self'),
        ]

    def __str__(self) -> str:
        return f'AccountGroup #{self.parent_id} -> #{self.child_id}'


class LoginHistory(models.Model):
    """ログイン履歴モデル"""
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='login_histories',
        verbose_name='ユーザー'
    )
    ip_address = models.GenericIPAddressField('IPアドレス', null=True, blank=True)
    user_agent = models.TextField('User-Agent', blank=True)
    location = models.CharField('アクセス元地域', max_length=200, blank=True)
    login_time = models.DateTimeField('ログイン日時', default=timezone.now)
    success = models.BooleanField('成功', default=True)
    
    class Meta:
        verbose_name = 'ログイン履歴'
        verbose_name_plural = 'ログイン履歴'
        ordering = ['-login_time']
    
    def __str__(self) -> str:
        status = "成功" if self.success else "失敗"
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')} ({status})"


class EmailVerificationToken(models.Model):
    """メールアドレス認証用トークンモデル"""
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='email_verification_tokens',
        verbose_name='ユーザー'
    )
    token = models.UUIDField(
        'トークン',
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    expires_at = models.DateTimeField('有効期限')
    is_verified = models.BooleanField('検証済み', default=False)
    
    class Meta:
        verbose_name = 'メール認証トークン'
        verbose_name_plural = 'メール認証トークン'
        ordering = ['-created_at']
    
    def save(self, *args: object, **kwargs: object) -> None:
        # 有効期限が設定されていない場合、作成から24時間後に設定
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        """トークンが有効かどうかをチェック"""
        return not self.is_verified and timezone.now() < self.expires_at

    def __str__(self) -> str:
        return f'{self.user.username} - {self.token}'
