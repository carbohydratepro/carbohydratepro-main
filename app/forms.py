from django import forms
from django.utils import timezone
from .models import Transaction, PaymentMethod, Category, VideoPost, Comment, Task, Memo, ShoppingItem

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'amount', 'purpose', 'transaction_type', 'category', 'major_category', 'payment_method']
        labels = {
            'date': '日付',
            'amount': '金額',
            'purpose': '用途',
            'transaction_type': '取引タイプ',
            'category': 'カテゴリ',
            'major_category': '費用タイプ',
            'payment_method': '支払方法',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control datepicker'}),
            'amount': forms.NumberInput(attrs={'step': '1', 'min': '0', 'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'major_category': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # 'user' キーワード引数を取得
        super(TransactionForm, self).__init__(*args, **kwargs)
        
        # 新規作成時はデフォルトで今日の日付を設定
        if not self.instance.pk and not self.data:
            self.fields['date'].initial = timezone.now().date()
        
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


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name']
        
    # bootstrap4対応で、classを指定
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'  
            
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        
        fields = ['name']
    # bootstrap4対応で、classを指定
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'  

# user：取引を行ったユーザー
# amount：金額
# date：取引日
# transaction_type：支出、収入、変動なし
# paymentmethod：支払方法（デフォルトは現金のみ、他はユーザーが登録できて選択式）
# purpose：用途、例（ステーキ）
# major_category：用途の大項目、例（固定費）（固定費、変動費、特別費）
# category：用途の項目、例（食費）（食費、娯楽、病院など、ユーザーが登録できて選択式）
# purpose_description：用途の詳細、例（○○で買った）


class DateForm(forms.Form):
    date = forms.DateField(widget=forms.TextInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))

class VideoPostForm(forms.ModelForm):
    class Meta:
        model = VideoPost
        fields = ['date', 'title', 'character', 'result', 'video_url', 'notes']
        error_messages = {
            'date': {
                'required': '日付を入力してください。',
            },
            'title': {
                'required': 'タイトルを入力してください。',
            },
            'character': {
                'required': '使用キャラを入力してください。',
            },
            'video_url': {
                'required': '動画URLを入力してください。',
            },
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'コメントを入力してください...', 'rows': 2})
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'task_type', 'frequency', 'priority', 'status', 'due_date', 'description']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # すべてのフィールドに 'form-control' クラスを追加
        for field_name, field in self.fields.items():
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        task_type = cleaned_data.get('task_type')
        frequency = cleaned_data.get('frequency')
        
        # 定期タスクの場合は頻度が必須
        if task_type == 'recurring' and not frequency:
            raise forms.ValidationError('定期タスクの場合、頻度を選択してください。')
        
        # 一時タスクの場合は頻度は不要
        if task_type == 'one_time' and frequency:
            cleaned_data['frequency'] = None
            
        return cleaned_data


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


class ShoppingItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingItem
        fields = ['title', 'frequency', 'price', 'remaining_count', 'memo']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'remaining_count': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
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