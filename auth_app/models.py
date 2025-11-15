from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_superuser(self, email, password=None, **extra_fields):
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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # 追加フィールド
    created_at = models.DateTimeField('作成日時', auto_now_add=True, null=True)
    last_login_at = models.DateTimeField('最終ログイン日時', null=True, blank=True)
    login_attempt_count = models.IntegerField('ログイン試行回数', default=0)
    access_count = models.IntegerField('アクセス数', default=0)
    
    # メールアドレス認証済みフラグ
    is_email_verified = models.BooleanField('メールアドレス認証済み', default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email or "未指定ユーザー"


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
    
    def __str__(self):
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
    
    def save(self, *args, **kwargs):
        # 有効期限が設定されていない場合、作成から24時間後に設定
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """トークンが有効かどうかをチェック"""
        return not self.is_verified and timezone.now() < self.expires_at
    
    def __str__(self):
        return f'{self.user.username} - {self.token}'
