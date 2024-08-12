from django import forms
from .models import Transaction, PaymentMethod, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'amount', 'purpose', 'transaction_type', 'category', 'major_category', 'payment_method']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '1.0'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # 'user' キーワード引数を取得
        super(TransactionForm, self).__init__(*args, **kwargs)
        if user is not None:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)
            self.fields['payment_method'].empty_label = None  # 空のラベルを非表示にする
            self.fields['payment_method'].required = True  # フィールドを必須にする
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['category'].empty_label = None  # 空のラベルを非表示にする
            self.fields['category'].required = True  # フィールドを必須にする

            
class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']




# user：取引を行ったユーザー
# amount：金額
# date：取引日
# transaction_type：支出、収入、変動なし
# paymentmethod：支払方法（デフォルトは現金のみ、他はユーザーが登録できて選択式）
# purpose：用途、例（ステーキ）
# major_category：用途の大項目、例（固定費）（固定費、変動費、特別費）
# category：用途の項目、例（食費）（食費、娯楽、病院など、ユーザーが登録できて選択式）
# purpose_description：用途の詳細、例（○○で買った）