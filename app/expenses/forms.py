from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Transaction, PaymentMethod, Category


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'amount', 'purpose', 'transaction_type', 'major_category', 'category', 'payment_method']
        labels = {
            'date': '日付',
            'purpose': '用途',
            'amount': '金額',
            'transaction_type': '取引タイプ',
            'category': 'カテゴリ',
            'major_category': '費用タイプ',
            'payment_method': '支払方法',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control datepicker'}),
            'amount': forms.NumberInput(attrs={'step': '1', 'min': '0', 'max': '99999999', 'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'major_category': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # 'user' キーワード引数を取得
        super(TransactionForm, self).__init__(*args, **kwargs)
        
        # 新規作成時はデフォルトで今日の日付を設定（日本時間）
        if not self.instance.pk and not self.data:
            self.fields['date'].initial = timezone.localtime(timezone.now()).date()
            self.fields['transaction_type'].initial = 'expense'
            self.fields['major_category'].initial = 'variable'
        
        # ユーザーに基づいてクエリセットをフィルタリング
        if user is not None:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)
            self.fields['payment_method'].empty_label = None  # 空のラベルを非表示にする
            self.fields['payment_method'].required = True  # フィールドを必須にする
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['category'].empty_label = None  # 空のラベルを非表示にする
            self.fields['category'].required = True  # フィールドを必須にする

        # すべてのフィールドに 'form-control' クラスを追加
        for field_name, field in self.fields.items():
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

        # 編集時に金額の小数点末尾を表示しないよう整形
        if self.instance.pk and self.instance.amount is not None:
            amount = Decimal(self.instance.amount)
            if amount == amount.to_integral_value():
                normalized = amount.quantize(Decimal('1'))
            else:
                normalized = amount.quantize(Decimal('0.01')).normalize()
            self.initial['amount'] = normalized
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None:
            if amount < 0:
                raise forms.ValidationError('金額は0以上である必要があります。')
            if amount > 99999999:
                raise forms.ValidationError('金額は99,999,999以下である必要があります。')
        return amount


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name']
        
    # bootstrap4対応で、classを指定
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['maxlength'] = '20'
        # エラーメッセージのカスタマイズ
        self.fields['name'].error_messages = {
            'max_length': '上限文字数は20です。',
            'required': 'この項目は必須です。',
        }
            

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        
        fields = ['name']
    # bootstrap4対応で、classを指定
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['maxlength'] = '20'
        # エラーメッセージのカスタマイズ
        self.fields['name'].error_messages = {
            'max_length': '上限文字数は20です。',
            'required': 'この項目は必須です。',
        }  
