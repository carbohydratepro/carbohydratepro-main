from django import forms
from .models import Memo


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
        super().__init__(*args, **kwargs)
        
        # すべてのフィールドに適切なクラスを設定
        for field_name, field in self.fields.items():
            if field_name != 'is_favorite':  # チェックボックスは除外
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
