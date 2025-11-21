from django import forms
from .models import ShoppingItem


class ShoppingItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingItem
        fields = ['title', 'frequency', 'price', 'remaining_count', 'threshold_count', 'memo']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'remaining_count': forms.NumberInput(attrs={'min': '0', 'max': '999', 'class': 'form-control'}),
            'threshold_count': forms.NumberInput(attrs={'min': '0', 'max': '999', 'class': 'form-control'}),
            'memo': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # すべてのフィールドに 'form-control' クラスを追加
        for field_name, field in self.fields.items():
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
