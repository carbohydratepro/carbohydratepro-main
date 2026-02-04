from django.contrib import admin
from .models import ContactMessage
from .expenses.models import Transaction, PaymentMethod, Category
from .memo.models import Memo
from .shopping.models import ShoppingItem
from .task.models import TaskLabel, Task


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('inquiry_type', 'subject', 'user', 'created_at', 'is_resolved')
    search_fields = ('subject', 'message', 'user__username', 'user__email')
    list_filter = ('inquiry_type', 'is_resolved', 'created_at')
    readonly_fields = ('created_at',)


# Expenses関連
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'transaction_type', 'amount', 'category', 'payment_method')
    search_fields = ('purpose', 'purpose_description', 'user__username')
    list_filter = ('transaction_type', 'major_category', 'date')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name', 'user__username')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name', 'user__username')


# Memo関連
@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ('title', 'memo_type', 'user', 'is_favorite', 'created_date', 'updated_date')
    search_fields = ('title', 'content', 'user__username')
    list_filter = ('memo_type', 'is_favorite', 'created_date')


# Shopping関連
@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'frequency', 'status', 'remaining_count', 'threshold_count', 'user')
    search_fields = ('title', 'memo', 'user__username')
    list_filter = ('frequency', 'status', 'user')


# Task関連
@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'user')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'label', 'status', 'priority', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'user__username')
    list_filter = ('status', 'priority', 'label', 'user', 'frequency')
