from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import CustomUser

class CustomUserAdmin(DefaultUserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_active', 'is_superuser')
    list_filter = ('is_active', 'is_superuser')
    fieldsets = (
        (None, {'fields': ['password']}),
        ('Personal info', {'fields': ['username', 'email']}),
        ('Permissions', {'fields': ['is_active', 'is_superuser', 'groups', 'user_permissions']}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ['username', 'email', 'password1', 'password2', 'is_active', 'is_superuser']}
        ),
    )
    search_fields = ('username', 'email')

admin.site.register(CustomUser, CustomUserAdmin)
