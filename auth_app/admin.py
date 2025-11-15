from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import CustomUser, LoginHistory, EmailVerificationToken


class LoginHistoryInline(admin.TabularInline):
    """ログイン履歴のインラインビュー"""
    model = LoginHistory
    extra = 0
    readonly_fields = ('login_time', 'ip_address', 'user_agent', 'location', 'success')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class CustomUserAdmin(DefaultUserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_email_verified', 'is_active', 'is_superuser', 
                    'created_at', 'last_login_at', 'login_attempt_count', 'access_count')
    list_filter = ('is_active', 'is_superuser', 'is_email_verified', 'created_at', 'last_login_at')
    fieldsets = (
        (None, {'fields': ['password']}),
        ('個人情報', {'fields': ['username', 'email', 'is_email_verified']}),
        ('権限', {'fields': ['is_active', 'is_superuser', 'is_staff', 'groups', 'user_permissions']}),
        ('重要な日時', {'fields': ['created_at', 'last_login_at']}),
        ('統計情報', {'fields': ['login_attempt_count', 'access_count']}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ['username', 'email', 'password1', 'password2', 'is_active', 'is_superuser']}
        ),
    )
    readonly_fields = ('created_at', 'last_login_at', 'login_attempt_count', 'access_count')
    search_fields = ('username', 'email')
    inlines = [LoginHistoryInline]


class LoginHistoryAdmin(admin.ModelAdmin):
    """ログイン履歴の管理画面"""
    list_display = ('user', 'login_time', 'ip_address', 'location', 'success', 'short_user_agent')
    list_filter = ('success', 'login_time', 'user')
    search_fields = ('user__username', 'user__email', 'ip_address', 'location')
    readonly_fields = ('user', 'login_time', 'ip_address', 'user_agent', 'location', 'success')
    date_hierarchy = 'login_time'
    ordering = ('-login_time',)
    
    def short_user_agent(self, obj):
        """User-Agentの短縮表示"""
        if len(obj.user_agent) > 50:
            return obj.user_agent[:50] + '...'
        return obj.user_agent
    short_user_agent.short_description = 'User-Agent'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(LoginHistory, LoginHistoryAdmin)


class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """メール認証トークンの管理画面"""
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_verified', 'is_valid_display')
    list_filter = ('is_verified', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('user', 'token', 'created_at', 'expires_at', 'is_verified')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def is_valid_display(self, obj):
        """トークンが有効かどうかの表示"""
        return obj.is_valid()
    is_valid_display.boolean = True
    is_valid_display.short_description = '有効'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)
