from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import LoginForm, SignupForm, UserUpdateForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm
from django.urls import reverse_lazy
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes



class TopView(generic.TemplateView):
    template_name = 'registration/top.html'
    
class Login(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'
    
'''自分しかアクセスできないようにするMixin(My Pageのため)'''
class OnlyYouMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        # 今ログインしてるユーザーのpkと、そのマイページのpkが同じなら許可
        user = self.request.user
        return user.pk == self.kwargs['pk']


'''マイページ'''
class MyPage(OnlyYouMixin, generic.DetailView):
    # ユーザーモデル取得
    User = get_user_model()
    model = User
    template_name = 'registration/my_page.html'
    # モデル名小文字(user)でモデルインスタンスがテンプレートファイルに渡される
    
'''サインアップ'''
class Signup(generic.CreateView):
    template_name = 'registration/user_form.html'
    form_class = SignupForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        
        # サインアップ後に自動的にログイン
        login(self.request, user)
        
        # ログイン後、通常のログインと同じ場所（家計簿）にリダイレクト
        return redirect('expense_list')
    
    # データ送信
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["process_name"] = "サインアップ"
        context["button_text"] = "サインアップ"
        return context


'''サインアップ完了'''
class SignupDone(generic.TemplateView):
    template_name = 'registration/signup_done.html'
    
    
'''ユーザー登録情報の更新'''
class Edit(OnlyYouMixin, generic.UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = 'registration/user_form.html'

    def get_success_url(self):
        return resolve_url('my_page', pk=self.kwargs['pk'])

    # contextデータ作成
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["process_name"] = "名前変更フォーム"
        context["button_text"] = "変更"
        return context

'''パスワード変更'''
class PasswordChange(PasswordChangeView):
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('password_change_done')
    template_name = 'registration/user_form.html'
    
    # contextデータ作成
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["process_name"] = "パスワード変更フォーム"
        context["button_text"] = "変更"
        return context


'''パスワード変更完了'''
class PasswordChangeDone(PasswordChangeDoneView):
    template_name = 'registration/passwordchange_done.html'


'''パスワードリセット申請'''
class PasswordReset(PasswordResetView):
    form_class = MyPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')
    subject_template_name = 'registration/password_reset_subject.txt'
    email_template_name = 'registration/password_reset_email.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["process_name"] = "パスワードリセット申請"
        context["button_text"] = "送信"
        return context
    
    def form_valid(self, form):
        """カスタムHTMLメール送信処理"""
        import logging
        from django.conf import settings
        
        logger = logging.getLogger(__name__)
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email}")
        
        # ユーザーを取得
        User = get_user_model()
        users = User.objects.filter(email__iexact=email, is_active=True)
        
        for user in users:
            # トークン生成
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # サイト情報をsettings.pyから取得
            domain = settings.SITE_DOMAIN
            site_name = settings.SITE_NAME
            protocol = settings.SITE_PROTOCOL
            
            # メールコンテキスト
            context = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': uid,
                'user': user,
                'token': token,
                'protocol': protocol,
            }
            
            # メール件名
            subject = render_to_string(self.subject_template_name, context)
            subject = ''.join(subject.splitlines())  # 改行を削除
            
            # HTMLメール本文
            html_message = render_to_string(self.email_template_name, context)
            
            # テキストメール本文（HTMLタグを除去）
            import re
            text_message = re.sub('<[^<]+?>', '', html_message)
            text_message = re.sub(r'\s+', ' ', text_message).strip()
            
            # HTMLメール送信
            try:
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email_message.attach_alternative(html_message, "text/html")
                email_message.send()
                
                logger.info(f"HTML email sent successfully to: {email}")
                
            except Exception as e:
                logger.error(f"Email sending failed for {email}: {str(e)}")
        
        return redirect(self.success_url)


'''パスワードリセット申請完了'''
class PasswordResetDone(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


'''パスワードリセット実行'''
class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = MySetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["process_name"] = "新しいパスワード設定"
        context["button_text"] = "変更"
        return context


'''パスワードリセット完了'''
class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
