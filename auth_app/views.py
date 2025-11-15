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
        from django.conf import settings
        from .models import EmailVerificationToken
        import logging
        
        logger = logging.getLogger(__name__)
        
        user = form.save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True  # アカウント自体はアクティブだが、メール未認証
        user.is_email_verified = False  # メールアドレスは未認証
        user.save()
        
        # メール認証トークンを生成
        token = EmailVerificationToken.objects.create(user=user)
        
        # 認証メールを送信
        try:
            verification_url = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/verify-email/{token.token}/"
            
            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': settings.SITE_NAME,
            }
            
            subject = f'{settings.SITE_NAME} - メールアドレスの確認'
            html_message = render_to_string('registration/email_verification.html', context)
            
            # テキスト版（HTMLタグを除去）
            import re
            text_message = re.sub('<[^<]+?>', '', html_message)
            text_message = re.sub(r'\s+', ' ', text_message).strip()
            
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()
            
            logger.info(f"Verification email sent to: {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        
        # サインアップ後に自動的にログインせず、メール確認ページにリダイレクト
        return redirect('signup_done')
    
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


'''メールアドレス認証'''
def verify_email(request, token):
    """メール認証トークンを検証するビュー"""
    from .models import EmailVerificationToken
    from django.contrib import messages
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        if verification_token.is_valid():
            # トークンが有効な場合、ユーザーのメールアドレスを認証済みにする
            user = verification_token.user
            user.is_email_verified = True
            user.save()
            
            # トークンを認証済みにする
            verification_token.is_verified = True
            verification_token.save()
            
            logger.info(f"Email verified for user: {user.email}")
            messages.success(request, 'メールアドレスの確認が完了しました。ログインしてください。')
            
            return redirect('login')
        else:
            # トークンが無効（期限切れまたは使用済み）
            logger.warning(f"Invalid or expired token: {token}")
            messages.error(request, 'このリンクは無効または期限切れです。')
            return redirect('signup')
            
    except EmailVerificationToken.DoesNotExist:
        logger.warning(f"Token not found: {token}")
        messages.error(request, '無効な認証リンクです。')
        return redirect('signup')


'''メール認証再送信'''
def resend_verification_email(request):
    """メール認証メールを再送信するビュー"""
    from django.conf import settings
    from .models import EmailVerificationToken
    from django.contrib import messages
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'メールアドレスを入力してください。')
            return redirect('resend_verification')
        
        try:
            User = get_user_model()
            user = User.objects.get(email=email, is_email_verified=False)
            
            # 既存の未使用トークンを無効化
            EmailVerificationToken.objects.filter(
                user=user,
                is_verified=False
            ).update(is_verified=True)
            
            # 新しいトークンを生成
            token = EmailVerificationToken.objects.create(user=user)
            
            # 認証メールを送信
            try:
                verification_url = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/verify-email/{token.token}/"
                
                context = {
                    'user': user,
                    'verification_url': verification_url,
                    'site_name': settings.SITE_NAME,
                }
                
                subject = f'{settings.SITE_NAME} - メールアドレスの確認'
                html_message = render_to_string('registration/email_verification.html', context)
                
                # テキスト版
                import re
                text_message = re.sub('<[^<]+?>', '', html_message)
                text_message = re.sub(r'\s+', ' ', text_message).strip()
                
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email_message.attach_alternative(html_message, "text/html")
                email_message.send()
                
                logger.info(f"Verification email resent to: {user.email}")
                messages.success(request, '確認メールを再送信しました。メールをご確認ください。')
                
            except Exception as e:
                logger.error(f"Failed to resend verification email to {user.email}: {str(e)}")
                messages.error(request, 'メール送信に失敗しました。時間をおいて再度お試しください。')
            
            return redirect('signup_done')
            
        except User.DoesNotExist:
            # セキュリティのため、ユーザーが存在しない場合も同じメッセージを表示
            messages.info(request, 'メールアドレスが登録されていないか、既に認証済みです。')
            return redirect('resend_verification')
    
    return render(request, 'registration/resend_verification.html')
