from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model # ユーザーモデルを取得するため
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm

'''ログイン用フォーム'''
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="メールアドレス")

    error_messages = {
        'invalid_login': "メールアドレスとパスワードが一致しません。",
        'inactive': "このアカウントは無効です。",
    }

    # bootstrap4対応
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる

'''サインアップ用フォーム'''
class SignupForm(UserCreationForm):
    username = forms.CharField(label="ユーザー名")
    email = forms.EmailField(label="メールアドレス")
    error_messages = {
        **UserCreationForm.error_messages,
        'duplicate_username': "このユーザー名は使われています。",
        'duplicate_email': "このメールアドレスは使われています。",
    }

    class Meta:
        model = get_user_model()
        fields = ('username', 'email')

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = '' # 全フィールドを入力必須

    def clean_username(self) -> str:
        username = self.cleaned_data.get('username')
        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError(self.error_messages['duplicate_username'], code='duplicate_username')
        return username

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError(self.error_messages['duplicate_email'], code='duplicate_email')
        return email


'''ユーザー情報更新用フォーム'''
class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(label="ユーザー名")
    email = forms.EmailField(label="メールアドレス")

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'avatar')

    # bootstrap4対応
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control-file' if field.widget.input_type == 'file' else 'form-control'
            if field.required:
                field.widget.attrs['required'] = ''


class AccountLinkLoginForm(forms.Form):
    email = forms.EmailField(label="メールアドレス")
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput)

    def __init__(self, *args: object, current_user: object | None = None, request: object | None = None, **kwargs: object) -> None:
        self.current_user = current_user
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = ''

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if not email or not password:
            return cleaned_data

        user = authenticate(self.request, username=email, password=password)
        if user is None:
            raise forms.ValidationError('メールアドレスとパスワードが一致しません。')
        if self.current_user is not None and user.pk == self.current_user.pk:
            raise forms.ValidationError('現在ログイン中のアカウントは追加できません。')
        if not user.is_active:
            raise forms.ValidationError('このアカウントは無効です。')
        if hasattr(user, 'is_email_verified') and not user.is_email_verified:
            raise forms.ValidationError('メール認証が完了していないアカウントは追加できません。')

        self.user = user
        return cleaned_data
            

'''パスワード変更フォーム'''
class MyPasswordChangeForm(PasswordChangeForm):

    # bootstrap4対応で、classを指定
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


'''パスワードリセット申請フォーム'''
class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="メールアドレス")

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


'''パスワードリセット実行フォーム'''
class MySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput
    )
    new_password2 = forms.CharField(
        label="新しいパスワード（確認用）",
        widget=forms.PasswordInput
    )
    
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
