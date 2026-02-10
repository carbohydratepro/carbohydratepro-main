from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Transaction, PaymentMethod, Category, RecurringPayment


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


DAY_OF_WEEK_CHOICES = [
    (0, '月'),
    (1, '火'),
    (2, '水'),
    (3, '木'),
    (4, '金'),
    (5, '土'),
    (6, '日'),
]

DAY_OF_MONTH_CHOICES = [(i, str(i)) for i in range(1, 32)]


class RecurringPaymentForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=DAY_OF_WEEK_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'day-of-week-selector'}),
        required=False,
        label='曜日（最大7つ）',
    )
    days_of_month = forms.MultipleChoiceField(
        choices=DAY_OF_MONTH_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'day-of-month-selector'}),
        required=False,
        label='日（最大7つ）',
    )

    class Meta:
        model = RecurringPayment
        fields = [
            'purpose', 'amount', 'transaction_type', 'major_category',
            'category', 'payment_method', 'purpose_description',
            'frequency', 'days_of_week', 'days_of_month', 'month_of_year',
        ]
        labels = {
            'purpose': '用途',
            'amount': '金額',
            'transaction_type': '取引タイプ',
            'major_category': '費用タイプ',
            'category': 'カテゴリ',
            'payment_method': '支払方法',
            'purpose_description': '説明',
            'frequency': '頻度',
            'month_of_year': '月',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '1', 'min': '0', 'max': '99999999', 'class': 'form-control',
            }),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'major_category': forms.Select(attrs={'class': 'form-control'}),
            'purpose_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'month_of_year': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '1', 'max': '12',
            }),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['month_of_year'].required = False

        self.fields['transaction_type'].initial = 'expense'
        self.fields['major_category'].initial = 'fixed'

        if user is not None:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)
            self.fields['payment_method'].empty_label = None
            self.fields['payment_method'].required = True
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['category'].empty_label = None
            self.fields['category'].required = True

        for field_name, field in self.fields.items():
            if field_name in ['days_of_week', 'days_of_month']:
                continue
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

        if self.instance.pk:
            if self.instance.amount is not None:
                amount = Decimal(self.instance.amount)
                if amount == amount.to_integral_value():
                    normalized = amount.quantize(Decimal('1'))
                else:
                    normalized = amount.quantize(Decimal('0.01')).normalize()
                self.initial['amount'] = normalized

            if self.instance.days_of_week:
                self.initial['days_of_week'] = [str(d) for d in self.instance.days_of_week]
            if self.instance.days_of_month:
                self.initial['days_of_month'] = [str(d) for d in self.instance.days_of_month]

    def clean_amount(self) -> Decimal:
        amount = self.cleaned_data.get('amount')
        if amount is not None:
            if amount < 0:
                raise forms.ValidationError('金額は0以上である必要があります。')
            if amount > 99999999:
                raise forms.ValidationError('金額は99,999,999以下である必要があります。')
        return amount

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')

        days_of_week = cleaned_data.get('days_of_week')
        days_of_month = cleaned_data.get('days_of_month')

        if frequency == 'weekly':
            if not days_of_week:
                self.add_error('days_of_week', '毎週の場合は曜日を1つ以上選択してください。')
            elif len(days_of_week) > 7:
                self.add_error('days_of_week', '曜日は最大7つまで選択できます。')
            else:
                cleaned_data['days_of_week'] = [int(d) for d in days_of_week]
        elif frequency == 'monthly':
            if not days_of_month:
                self.add_error('days_of_month', '毎月の場合は日を1つ以上選択してください。')
            elif len(days_of_month) > 7:
                self.add_error('days_of_month', '日は最大7つまで選択できます。')
            else:
                cleaned_data['days_of_month'] = [int(d) for d in days_of_month]
                for day in cleaned_data['days_of_month']:
                    if day < 1 or day > 31:
                        self.add_error('days_of_month', '日は1〜31の範囲で指定してください。')
                        break
        elif frequency == 'yearly':
            if not cleaned_data.get('month_of_year'):
                self.add_error('month_of_year', '毎年の場合は月を指定してください。')
            if not days_of_month:
                self.add_error('days_of_month', '毎年の場合は日を1つ以上選択してください。')
            elif len(days_of_month) > 7:
                self.add_error('days_of_month', '日は最大7つまで選択できます。')
            else:
                cleaned_data['days_of_month'] = [int(d) for d in days_of_month]
                for day in cleaned_data['days_of_month']:
                    if day < 1 or day > 31:
                        self.add_error('days_of_month', '日は1〜31の範囲で指定してください。')
                        break

        if cleaned_data.get('month_of_year') is not None:
            month = cleaned_data['month_of_year']
            if month < 1 or month > 12:
                self.add_error('month_of_year', '月は1〜12の範囲で指定してください。')

        if frequency == 'daily':
            cleaned_data['days_of_week'] = []
            cleaned_data['days_of_month'] = []

        return cleaned_data
