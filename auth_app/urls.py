from django.urls import path
from . import views, demo_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.Login.as_view(), name='login'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('top/', views.TopView.as_view(), name='top'),
    # デモ画面
    path('demo/', demo_views.demo_redirect, name='demo'),
    path('demo/expenses/', demo_views.demo_expenses, name='demo_expenses'),
    path('demo/tasks/', demo_views.demo_tasks, name='demo_tasks'),
    path('demo/habits/', demo_views.demo_habits, name='demo_habits'),
    path('demo/memos/', demo_views.demo_memos, name='demo_memos'),
    path('demo/shopping/', demo_views.demo_shopping, name='demo_shopping'),
    path('demo/board/', demo_views.demo_board, name='demo_board'),
    path('demo/settings/expenses/', demo_views.demo_expenses_settings, name='demo_expenses_settings'),
    path('demo/settings/tasks/', demo_views.demo_task_settings, name='demo_task_settings'),
    path('demo/settings/memos/', demo_views.demo_memo_settings, name='demo_memo_settings'),
    path('demo/habits/list/', demo_views.demo_habit_list, name='demo_habit_list'),
    path('demo/expenses/recurring/', demo_views.demo_recurring_payments, name='demo_recurring_payments'),
    path('my_page/<int:pk>/', views.MyPage.as_view(), name='my_page'),
    path('signup/', views.Signup.as_view(), name='signup'),
    path('signup_done/', views.SignupDone.as_view(), name='signup_done'),
    path('edit/<int:pk>', views.Edit.as_view(), name='edit'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'), # パスワード変更
    path('password_change_done/', views.PasswordChangeDone.as_view(), name='password_change_done'), # パスワード変更完了
    # パスワードリセット機能
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset_done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    # メール認証機能
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
]