from django import forms

from .models import Habit


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['title', 'frequency', 'is_positive', 'coefficient', 'weekly_goal', 'monthly_goal']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '100',
                'placeholder': '例: 読書、運動、飲酒...',
            }),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'is_positive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '1',
                'max': '10',
            }),
            'weekly_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '7',
                'placeholder': '0=目標なし',
            }),
            'monthly_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '31',
                'placeholder': '0=目標なし',
            }),
        }
        labels = {
            'title': '習慣名',
            'frequency': '頻度',
            'is_positive': '良い習慣（緑）',
            'coefficient': '係数（1〜10）',
            'weekly_goal': '週の目標回数',
            'monthly_goal': '月の目標回数',
        }
        help_texts = {
            'is_positive': 'チェックあり=良い習慣（緑/プラス）、チェックなし=悪い習慣（赤/マイナス）',
            'coefficient': '習慣の重みづけ（大きいほど影響大）',
            'weekly_goal': '0 は目標なし',
            'monthly_goal': '0 は目標なし',
        }
