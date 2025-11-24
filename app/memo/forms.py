from django import forms
from django.db import models
from .models import Memo, MemoType


class MemoTypeForm(forms.ModelForm):
    class Meta:
        model = MemoType
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }


class MemoForm(forms.ModelForm):
    class Meta:
        model = Memo
        fields = ['title', 'memo_type', 'content', 'is_favorite']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'memo_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # メモ種別をユーザー専用＋共通で絞り込み
        if user:
            self.fields['memo_type'].queryset = MemoType.objects.filter(models.Q(user=user) | models.Q(user__isnull=True)).order_by('name')

        # デフォルト選択を「メモ」に合わせる
        if not self.instance.pk and not self.data:
            memo_type = self.fields['memo_type'].queryset.filter(name='メモ').first()
            if memo_type:
                self.fields['memo_type'].initial = memo_type

        # すべてのフィールドに適切なクラスを設定
        for field_name, field in self.fields.items():
            if field_name != 'is_favorite':  # チェックボックスは除外
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
