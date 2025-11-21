from django import forms
from django.utils import timezone
from .models import Task, TaskLabel


class TaskLabelForm(forms.ModelForm):
    class Meta:
        model = TaskLabel
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '30'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # エラーメッセージのカスタマイズ
        self.fields['name'].error_messages = {
            'max_length': '上限文字数は30です。',
            'required': 'この項目は必須です。',
        }


class TaskForm(forms.ModelForm):
    # 終日チェックボックス用の追加フィールド
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'step': '300'}),  # 5分刻み
        label='開始時刻'
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'step': '300'}),  # 5分刻み
        label='終了時刻'
    )
    
    class Meta:
        model = Task
        fields = ['title', 'frequency', 'repeat_interval', 'repeat_count', 'priority', 'status', 'label', 
                  'start_date', 'end_date', 'all_day', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'all_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '200'}),
            'repeat_interval': forms.NumberInput(attrs={'min': '1', 'max': '99', 'class': 'form-control', 'value': '1'}),
            'repeat_count': forms.NumberInput(attrs={'min': '1', 'max': '999', 'class': 'form-control'}),
        }
        labels = {
            'title': 'タイトル',
            'frequency': '頻度',
            'repeat_interval': '間隔',
            'repeat_count': '繰り返し回数',
            'priority': '優先度',
            'status': 'ステータス',
            'label': 'ラベル',
            'start_date': '開始日',
            'end_date': '終了日',
            'all_day': '終日',
            'description': '詳細',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # ユーザーに基づいてラベルのクエリセットをフィルタリング
        if user is not None:
            self.fields['label'].queryset = TaskLabel.objects.filter(user=user)
            self.fields['label'].empty_label = 'ラベルなし'
            self.fields['label'].required = False
        
        # 既存のインスタンスがある場合、時刻フィールドを初期化
        if self.instance.pk:
            if self.instance.start_date and not self.instance.all_day:
                self.fields['start_time'].initial = self.instance.start_date.time()
            if self.instance.end_date and not self.instance.all_day:
                self.fields['end_time'].initial = self.instance.end_date.time()
        
        # すべてのフィールドに 'form-control' クラスを追加
        for field_name, field in self.fields.items():
            if field_name == 'all_day':  # チェックボックスは除外
                continue
            if 'class' in field.widget.attrs:
                if 'form-control' not in field.widget.attrs['class']:
                    field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        repeat_interval = cleaned_data.get('repeat_interval')
        repeat_count = cleaned_data.get('repeat_count')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        all_day = cleaned_data.get('all_day')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # 頻度が選択されている場合、繰り返し回数は必須
        if frequency and frequency != '':
            if not repeat_interval:
                raise forms.ValidationError('頻度を選択した場合、間隔を入力してください。')
            if not repeat_count:
                raise forms.ValidationError('頻度を選択した場合、繰り返し回数を入力してください。')
        
        # 終日でない場合、時刻が必要
        if not all_day:
            if start_date and not start_time:
                raise forms.ValidationError('開始日が選択されている場合、開始時刻も入力してください（または終日にチェックを入れてください）。')
            if end_date and not end_time:
                raise forms.ValidationError('終了日が選択されている場合、終了時刻も入力してください（または終日にチェックを入れてください）。')
        
        # 開始日時と終了日時の組み合わせ
        if start_date and end_date:
            if all_day:
                # 終日の場合、時刻を00:00に設定
                from datetime import time
                cleaned_data['start_date'] = timezone.make_aware(
                    timezone.datetime.combine(start_date, time(0, 0))
                )
                cleaned_data['end_date'] = timezone.make_aware(
                    timezone.datetime.combine(end_date, time(23, 59))
                )
            else:
                # 終日でない場合、時刻を結合
                if start_time and end_time:
                    cleaned_data['start_date'] = timezone.make_aware(
                        timezone.datetime.combine(start_date, start_time)
                    )
                    cleaned_data['end_date'] = timezone.make_aware(
                        timezone.datetime.combine(end_date, end_time)
                    )
            
            # 終了日時が開始日時より前でないかチェック
            if cleaned_data['end_date'] < cleaned_data['start_date']:
                if all_day:
                    raise forms.ValidationError('終了日は開始日と同じか、それより後の日付を選択してください。')
                else:
                    raise forms.ValidationError('終了時刻は開始時刻より後に設定してください。')
        
        return cleaned_data
