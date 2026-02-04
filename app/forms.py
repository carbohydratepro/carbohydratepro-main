from django import forms
from .models import ContactMessage

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

