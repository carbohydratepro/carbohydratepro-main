"""検出イベントと通知状態。ログ本文や秘密値は保存しない。"""
from django.db import models
from django.utils import timezone


class SecurityEvent(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True)
    occurred_at = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=16)
    category = models.CharField(max_length=48, db_index=True)
    severity = models.CharField(max_length=12)
    summary = models.CharField(max_length=200)

    class Meta:
        ordering = ['-occurred_at', '-id']
        indexes = [models.Index(fields=['category', 'occurred_at'], name='security_category_time')]


class SecurityMonitorState(models.Model):
    name = models.CharField(max_length=32, unique=True)
    started_at = models.DateTimeField(default=timezone.now)
    checked_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=200, blank=True)


class SecurityAlertState(models.Model):
    signature = models.CharField(max_length=48, unique=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_event_id = models.BigIntegerField(default=0)
