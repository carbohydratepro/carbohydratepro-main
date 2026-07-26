from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

COOKING_IMAGE_MAX_SIZE = 5 * 1024 * 1024
COOKING_IMAGE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
COOKING_IMAGE_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_cooking_image(uploaded_file: Any) -> None:
    """料理写真のサイズと実ファイル形式を検証する。"""
    if getattr(uploaded_file, "size", 0) > COOKING_IMAGE_MAX_SIZE:
        raise ValidationError("写真は1枚5MB以下にしてください。")

    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    if extension not in COOKING_IMAGE_ALLOWED_EXTENSIONS:
        raise ValidationError("写真はJPEG、PNG、WebP形式のみ利用できます。")

    content_type = getattr(uploaded_file, "content_type", "")
    if content_type and content_type not in COOKING_IMAGE_ALLOWED_CONTENT_TYPES:
        raise ValidationError("写真はJPEG、PNG、WebP形式のみ利用できます。")

    position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else None
    header = uploaded_file.read(16) if hasattr(uploaded_file, "read") else b""
    if position is not None and hasattr(uploaded_file, "seek"):
        uploaded_file.seek(position)

    is_jpeg = header.startswith(b"\xff\xd8\xff")
    is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if header and not (is_jpeg or is_png or is_webp):
        raise ValidationError("写真の画像形式を確認できません。")


def cooking_image_upload_to(instance: models.Model, filename: str) -> str:
    """ユーザー単位の予測困難なファイル名で料理写真を保存する。"""
    dish = getattr(instance, "dish", instance)
    user_id = getattr(dish, "user_id", "unknown") or "unknown"
    extension = Path(filename).suffix.lower()
    return f"cooking/{user_id}/{uuid.uuid4().hex}{extension}"


class CookingDish(models.Model):
    RECIPE_SINGLE = "single"
    RECIPE_STEPS = "steps"
    RECIPE_MODE_CHOICES = [
        (RECIPE_SINGLE, "一括メモ"),
        (RECIPE_STEPS, "手順ごと"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cooking_dishes",
        verbose_name="ユーザー",
    )
    title = models.CharField(max_length=200, verbose_name="料理名")
    ingredients = models.TextField(blank=True, verbose_name="材料リスト")
    recipe_mode = models.CharField(
        max_length=10,
        choices=RECIPE_MODE_CHOICES,
        default=RECIPE_SINGLE,
        verbose_name="レシピ形式",
    )
    recipe_text = models.TextField(blank=True, verbose_name="レシピ")
    servings = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        verbose_name="分量（人分）",
    )
    cooking_time_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        verbose_name="所要時間（分）",
    )
    notes = models.TextField(blank=True, verbose_name="メモ")
    is_favorite = models.BooleanField(default=False, verbose_name="お気に入り")
    photo_1 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="料理写真1",
    )
    photo_2 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="料理写真2",
    )
    photo_3 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="料理写真3",
    )
    photo_4 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="料理写真4",
    )
    photo_5 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="料理写真5",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["-is_favorite", "-updated_at", "-pk"]
        verbose_name = "料理"
        verbose_name_plural = "料理"
        indexes = [
            models.Index(fields=["user", "updated_at"], name="cook_user_updated_idx"),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def photos(self) -> list[Any]:
        return [photo for photo in self._photo_values() if photo]

    @property
    def cover_photo(self) -> Any | None:
        return next((photo for photo in self._photo_values() if photo), None)

    def _photo_values(self) -> list[Any]:
        return [self.photo_1, self.photo_2, self.photo_3, self.photo_4, self.photo_5]


class CookingStep(models.Model):
    dish = models.ForeignKey(
        CookingDish,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name="料理",
    )
    position = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="手順番号",
    )
    instruction = models.TextField(verbose_name="手順")
    photo_1 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="手順写真1",
    )
    photo_2 = models.FileField(
        upload_to=cooking_image_upload_to,
        blank=True,
        validators=[validate_cooking_image],
        verbose_name="手順写真2",
    )

    class Meta:
        ordering = ["position", "pk"]
        verbose_name = "料理手順"
        verbose_name_plural = "料理手順"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(position__gte=1) & models.Q(position__lte=10),
                name="cooking_step_position_1_10",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.dish.title} - 手順{self.position}"

    @property
    def photos(self) -> list[Any]:
        return [photo for photo in (self.photo_1, self.photo_2) if photo]


class CookingHistory(models.Model):
    dish = models.ForeignKey(
        CookingDish,
        on_delete=models.CASCADE,
        related_name="histories",
        verbose_name="料理",
    )
    cooked_on = models.DateField(verbose_name="作った日")
    count = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(999)],
        verbose_name="回数",
    )
    note = models.CharField(max_length=200, blank=True, verbose_name="メモ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["-cooked_on", "-pk"]
        verbose_name = "料理作成履歴"
        verbose_name_plural = "料理作成履歴"
        constraints = [
            models.UniqueConstraint(fields=["dish", "cooked_on"], name="unique_cooking_day"),
            models.CheckConstraint(
                condition=models.Q(count__gte=1) & models.Q(count__lte=999),
                name="cooking_history_count_1_999",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.dish.title} - {self.cooked_on} ({self.count}回)"
