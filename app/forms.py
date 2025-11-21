from django import forms
from .models import VideoPost, Comment, ContactMessage

from .expenses.forms import TransactionForm, PaymentMethodForm, CategoryForm
from .memo.forms import MemoForm
from .shopping.forms import ShoppingItemForm
from .task.forms import TaskForm, TaskLabelForm

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["inquiry_type", "subject", "message"]
        labels = {
            "inquiry_type": "お問い合わせの種類",
            "subject": "件名",
            "message": "お問い合わせ内容",
        }
        widgets = {
            "inquiry_type": forms.Select(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "件名を入力してください"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 8, "placeholder": "お問い合わせ内容を詳しくご記入ください"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class DateForm(forms.Form):
    date = forms.DateField(widget=forms.TextInput(attrs={"type": "date", "class": "form-control"}))

class VideoPostForm(forms.ModelForm):
    class Meta:
        model = VideoPost
        fields = ["date", "title", "character", "result", "video_url", "notes"]
        error_messages = {
            "date": {"required": "日付を入力してください。"},
            "title": {"required": "タイトルを入力してください。"},
            "character": {"required": "使用キャラを入力してください。"},
            "video_url": {"required": "動画URLを入力してください。"},
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {"content": forms.Textarea(attrs={"placeholder": "コメントを入力してください...", "rows": 2})}