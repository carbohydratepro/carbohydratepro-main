from __future__ import annotations

from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import CookingDish, CookingHistory, CookingStep

MAX_TOTAL_UPLOAD_SIZE = 80 * 1024 * 1024
IMAGE_ACCEPT = "image/jpeg,image/png,image/webp"


class CookingDishForm(forms.ModelForm):
    class Meta:
        model = CookingDish
        fields = [
            "title",
            "ingredients",
            "servings",
            "cooking_time_minutes",
            "recipe_mode",
            "recipe_text",
            "notes",
            "is_favorite",
            "photo_1",
            "photo_2",
            "photo_3",
            "photo_4",
            "photo_5",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "maxlength": "200", "autofocus": True}
            ),
            "ingredients": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": "例:\n鶏もも肉 300g\n玉ねぎ 1個",
                }
            ),
            "servings": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "99"}),
            "cooking_time_minutes": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "1440"}
            ),
            "recipe_mode": forms.RadioSelect(attrs={"data-recipe-mode": ""}),
            "recipe_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 12,
                    "placeholder": "作り方をまとめて入力してください",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "次回変えたい点や家族の感想など",
                }
            ),
            "is_favorite": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["servings"].widget.attrs["min"] = "1"
        self.fields["cooking_time_minutes"].widget.attrs["min"] = "1"
        for index in range(1, 6):
            field = self.fields[f"photo_{index}"]
            field.widget.attrs.update(
                {"class": "form-control-file cooking-photo-input", "accept": IMAGE_ACCEPT}
            )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        total_size = sum(getattr(uploaded, "size", 0) for uploaded in self.files.values())
        if total_size > MAX_TOTAL_UPLOAD_SIZE:
            raise ValidationError("1回に送信できる写真の合計は80MBまでです。")
        return cleaned_data


class CookingStepForm(forms.ModelForm):
    class Meta:
        model = CookingStep
        fields = ["position", "instruction", "photo_1", "photo_2"]
        widgets = {
            "position": forms.HiddenInput(),
            "instruction": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "この手順の内容を入力してください",
                }
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for index in range(1, 3):
            field = self.fields[f"photo_{index}"]
            field.widget.attrs.update(
                {"class": "form-control-file cooking-photo-input", "accept": IMAGE_ACCEPT}
            )


class BaseCookingStepFormSet(BaseInlineFormSet):
    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return

        active_count = 0
        for form in self.forms:
            cleaned_data = getattr(form, "cleaned_data", {})
            if not cleaned_data or cleaned_data.get("DELETE"):
                continue
            instruction = str(cleaned_data.get("instruction") or "").strip()
            has_photo = bool(cleaned_data.get("photo_1") or cleaned_data.get("photo_2"))
            if has_photo and not instruction:
                form.add_error("instruction", "写真を登録する手順には本文を入力してください。")
            if instruction:
                active_count += 1

        if active_count > 10:
            raise ValidationError("手順は10個まで登録できます。")
        if self.instance.recipe_mode == CookingDish.RECIPE_STEPS and active_count == 0:
            raise ValidationError("手順ごとに記録する場合は、手順を1つ以上入力してください。")


CookingStepFormSet = inlineformset_factory(
    CookingDish,
    CookingStep,
    form=CookingStepForm,
    formset=BaseCookingStepFormSet,
    fields=["position", "instruction", "photo_1", "photo_2"],
    extra=1,
    can_delete=True,
    max_num=10,
    validate_max=True,
)


class CookingHistoryForm(forms.ModelForm):
    class Meta:
        model = CookingHistory
        fields = ["cooked_on", "count", "note"]
        widgets = {
            "cooked_on": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "count": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "999"}),
            "note": forms.TextInput(
                attrs={"class": "form-control", "maxlength": "200", "placeholder": "任意のメモ"}
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["count"].widget.attrs["min"] = "1"
