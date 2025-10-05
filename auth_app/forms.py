from django import forms
from django.contrib.auth import get_user_model # ユーザーモデルを取得するため
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm

'''ログイン用フォーム'''
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="ユーザー名")

    # bootstrap4対応
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる

'''サインアップ用フォーム'''
class SignupForm(UserCreationForm):
    username = forms.CharField(label="ユーザー名")
    email = forms.EmailField(label="メールアドレス")

    class Meta:
        model = get_user_model()
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = '' # 全フィールドを入力必須      

'''ユーザー情報更新用フォーム'''
class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(label="ユーザー名")
    email = forms.EmailField(label="メールアドレス")
    
    class Meta:
        model = get_user_model()
        fields = ('username', 'email')

    # bootstrap4対応
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = '' # 全フィールドを入力必須
            

'''パスワード変更フォーム'''
class MyPasswordChangeForm(PasswordChangeForm):

    # bootstrap4対応で、classを指定
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


'''パスワードリセット申請フォーム'''
class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="メールアドレス")
    
    def __init__(self, *args, **kwargs):
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label