import logging
from urllib.parse import urlencode

from django.contrib.auth.views import (
    LoginView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.shortcuts import render, redirect, resolve_url
from django.views import generic
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import (
    AccountLinkLoginForm,
    LoginForm,
    MyPasswordChangeForm,
    MyPasswordResetForm,
    MySetPasswordForm,
    SignupForm,
    UserUpdateForm,
)
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib import messages

from project.utils import send_html_email, strip_html_tags
from . import services

logger = logging.getLogger(__name__)


def send_verification_email(user) -> bool:
    """メール認証リンクを送信する。"""
    from .models import EmailVerificationToken

    token = EmailVerificationToken.objects.create(user=user)
    verification_url = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/verify-email/{token.token}/"
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': settings.SITE_NAME,
    }
    return send_html_email(
        subject=f'{settings.SITE_NAME} - メールアドレスの確認',
        template_name='registration/email_verification.html',
        context=context,
        recipient_list=[user.email],
    )



class TopView(generic.TemplateView):
    template_name = 'registration/top.html'


class Login(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'

    def get_initial(self):
        initial = super().get_initial()
        email = self.request.GET.get('email')
        if email:
            initial['username'] = email
        return initial

    def form_valid(self, form):
        restore_group = None
        restore_active_user_ids = None
        if self.request.GET.get('account_switch') == '1':
            restore_group = services.get_session_account_group(self.request)
            if restore_group is not None:
                restore_active_user_ids = services.get_active_account_user_ids(self.request, restore_group)

        response = super().form_valid(form)
        if restore_group is not None and restore_active_user_ids is not None:
            services.restore_account_session(
                self.request,
                restore_group,
                restore_active_user_ids,
                authenticated_user=form.get_user(),
            )
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.GET.get('account_switch') != '1':
            return redirect(resolve_url('top'))
        return super().dispatch(request, *args, **kwargs)
    
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
        user.is_active = True  # アカウント自体はアクティブだが、メール未認証
        user.is_email_verified = False  # メールアドレスは未認証
        user.save()

        # デフォルトデータを生成
        services.create_default_user_data(user)

        send_verification_email(user)

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
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email}")

        # ユーザーを取得
        User = get_user_model()
        users = User.objects.filter(email__iexact=email, is_active=True)

        for user in users:
            # トークン生成
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # メールコンテキスト
            context = {
                'email': user.email,
                'domain': settings.SITE_DOMAIN,
                'site_name': settings.SITE_NAME,
                'uid': uid,
                'user': user,
                'token': token,
                'protocol': settings.SITE_PROTOCOL,
            }

            # メール件名
            subject = render_to_string(self.subject_template_name, context)
            subject = ''.join(subject.splitlines())  # 改行を削除

            send_html_email(
                subject=subject,
                template_name=self.email_template_name,
                context=context,
                recipient_list=[user.email],
            )

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


def account_edit(request):
    """セッション内で有効なアカウントの切替と解除を管理する。"""
    memberships = services.get_account_memberships(request)
    if not memberships:
        messages.info(request, '切り替え可能なアカウントがありません。ログインしてください。')
        return redirect('login')

    group = services.get_session_account_group(request)
    active_user_ids = services.get_active_account_user_ids(request, group) if group is not None else []
    return render(
        request,
        'registration/account_select.html',
        {
            'active_user_ids': active_user_ids,
            'memberships': memberships,
        },
    )


account_select = account_edit


def _login_with_account_session(request, user, group, active_user_ids: list[int]) -> None:
    """Djangoログインでセッションが更新された後、アカウント切替状態を戻す。"""
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    services.restore_account_session(request, group, active_user_ids, authenticated_user=user)


@login_required
def account_add(request):
    """既存アカウントを現在のグループへ追加する。"""
    existing_form = AccountLinkLoginForm(
        prefix='existing',
        current_user=request.user,
        request=request,
    )

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type in ('existing', None, ''):
            existing_form = AccountLinkLoginForm(
                request.POST,
                prefix='existing',
                current_user=request.user,
                request=request,
            )
            if existing_form.is_valid() and existing_form.user is not None:
                target_user = existing_form.user
                group = services.link_accounts(request.user, target_user, created_by=request.user)
                services.remember_account_group(request, group)
                services.activate_group_accounts(request, group)
                active_user_ids = services.get_active_account_user_ids(request, group)
                _login_with_account_session(request, target_user, group, active_user_ids)
                messages.success(request, f'{target_user.username} に切り替えました。')
                return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, 'このアカウント追加方法は現在利用できません。')

    return render(
        request,
        'registration/account_add.html',
        {
            'existing_form': existing_form,
        },
    )


@require_POST
def account_switch(request, pk: int):
    """セッション内で有効なアカウントへ切り替える。"""
    group = services.get_session_account_group(request)
    memberships = services.get_account_memberships(request)
    target_membership = next((membership for membership in memberships if membership.user_id == pk), None)
    if group is None or target_membership is None:
        messages.error(request, 'このアカウントには切り替えできません。')
        return redirect('account_edit' if memberships else 'login')

    target_user = target_membership.user
    active_user_ids = services.get_active_account_user_ids(request, group)
    if target_user.pk not in active_user_ids or not request.user.is_authenticated:
        messages.info(request, '切り替え先のアカウントでログインしてください。')
        login_url = reverse('login')
        query = urlencode({
            'account_switch': '1',
            'email': target_user.email,
            'next': settings.LOGIN_REDIRECT_URL,
        })
        return redirect(f'{login_url}?{query}')

    _login_with_account_session(request, target_user, group, active_user_ids)
    messages.success(request, f'{target_user.username} に切り替えました。')
    return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
@require_POST
def account_remove(request, pk: int):
    """現在アカウント以外をアカウントグループから解除する。"""
    User = get_user_model()
    target_user = User.objects.filter(pk=pk).first()
    if target_user is None:
        messages.error(request, '解除対象のアカウントが見つかりません。')
        return redirect('account_edit')

    if services.remove_account_from_group(request.user, target_user, request=request):
        messages.success(request, f'{target_user.username} をアカウント切替から解除しました。')
    else:
        messages.error(request, '現在のアカウントは解除できません。')
    return redirect('account_edit')


@require_POST
def account_logout_current(request):
    """現在のアカウントだけをログアウトする。"""
    if not request.user.is_authenticated:
        return redirect('login')

    remaining_memberships = services.deactivate_current_account(request, request.user)
    if not remaining_memberships:
        logout(request)
        return redirect('login')

    group = remaining_memberships[0].group
    active_user_ids = services.get_active_account_user_ids(request, group)
    next_user = remaining_memberships[0].user
    _login_with_account_session(request, next_user, group, active_user_ids)
    messages.success(request, f'現在のアカウントからログアウトし、{next_user.username} に切り替えました。')
    return redirect(settings.LOGIN_REDIRECT_URL)


'''メールアドレス認証'''
def verify_email(request, token):
    """メール認証トークンを検証するビュー"""
    from .models import EmailVerificationToken

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
            messages.success(request, 'メールアドレスの確認が完了しました。')

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
    from .models import EmailVerificationToken

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
            verification_url = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/verify-email/{token.token}/"
            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': settings.SITE_NAME,
            }

            if send_html_email(
                subject=f'{settings.SITE_NAME} - メールアドレスの確認',
                template_name='registration/email_verification.html',
                context=context,
                recipient_list=[user.email],
            ):
                messages.success(request, '確認メールを再送信しました。メールをご確認ください。')
            else:
                messages.error(request, 'メール送信に失敗しました。時間をおいて再度お試しください。')

            return redirect('signup_done')

        except User.DoesNotExist:
            # セキュリティのため、ユーザーが存在しない場合も同じメッセージを表示
            messages.info(request, 'メールアドレスが登録されていないか、既に認証済みです。')
            return redirect('resend_verification')

    return render(request, 'registration/resend_verification.html')
