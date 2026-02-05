"""
支出管理機能のテスト
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from app.expenses.models import Category, PaymentMethod, Transaction
from app.expenses.forms import TransactionForm, PaymentMethodForm, CategoryForm


class PaymentMethodModelTest(TestCase):
    """支払方法モデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )

    def test_create_payment_method(self) -> None:
        """支払方法の作成テスト"""
        payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='現金'
        )
        self.assertEqual(str(payment_method), '現金')
        self.assertEqual(payment_method.user, self.user)

    def test_payment_method_max_length(self) -> None:
        """支払方法名の最大文字数テスト"""
        payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='A' * 20
        )
        self.assertEqual(len(payment_method.name), 20)


class CategoryModelTest(TestCase):
    """カテゴリモデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )

    def test_create_category(self) -> None:
        """カテゴリの作成テスト"""
        category = Category.objects.create(
            user=self.user,
            name='食費'
        )
        self.assertEqual(str(category), '食費')
        self.assertEqual(category.user, self.user)


class TransactionModelTest(TestCase):
    """取引モデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='現金'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='食費'
        )

    def test_create_expense_transaction(self) -> None:
        """支出取引の作成テスト"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='昼食',
            major_category='variable',
            category=self.category,
            purpose_description='会社近くのレストランで昼食'
        )
        self.assertEqual(transaction.transaction_type, 'expense')
        self.assertEqual(transaction.amount, Decimal('1000.00'))
        self.assertIn('test@example.com', str(transaction))

    def test_create_income_transaction(self) -> None:
        """収入取引の作成テスト"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('300000.00'),
            date=timezone.now(),
            transaction_type='income',
            payment_method=self.payment_method,
            purpose='給与',
            major_category='fixed',
            category=self.category,
            purpose_description='月給'
        )
        self.assertEqual(transaction.transaction_type, 'income')

    def test_major_category_choices(self) -> None:
        """大分類の選択肢テスト"""
        choices = dict(Transaction.MAJOR_CATEGORY_TYPE_CHOICES)
        self.assertIn('variable', choices)
        self.assertIn('fixed', choices)
        self.assertIn('special', choices)


class TransactionFormTest(TestCase):
    """取引フォームのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='現金'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='食費'
        )

    def test_valid_form(self) -> None:
        """有効なフォームデータのテスト"""
        form_data = {
            'date': timezone.now().date(),
            'amount': 1000,
            'purpose': '昼食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_negative_amount_invalid(self) -> None:
        """負の金額が無効であることをテスト"""
        form_data = {
            'date': timezone.now().date(),
            'amount': -100,
            'purpose': '昼食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_amount_exceeds_max_invalid(self) -> None:
        """金額上限超過が無効であることをテスト"""
        form_data = {
            'date': timezone.now().date(),
            'amount': 100000000,
            'purpose': '昼食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_default_values_on_new_form(self) -> None:
        """新規フォームのデフォルト値テスト"""
        form = TransactionForm(user=self.user)
        self.assertEqual(form.fields['transaction_type'].initial, 'expense')
        self.assertEqual(form.fields['major_category'].initial, 'variable')


class PaymentMethodFormTest(TestCase):
    """支払方法フォームのテスト"""

    def test_valid_form(self) -> None:
        """有効なフォームデータのテスト"""
        form = PaymentMethodForm(data={'name': '現金'})
        self.assertTrue(form.is_valid())

    def test_empty_name_invalid(self) -> None:
        """空の名前が無効であることをテスト"""
        form = PaymentMethodForm(data={'name': ''})
        self.assertFalse(form.is_valid())


class CategoryFormTest(TestCase):
    """カテゴリフォームのテスト"""

    def test_valid_form(self) -> None:
        """有効なフォームデータのテスト"""
        form = CategoryForm(data={'name': '食費'})
        self.assertTrue(form.is_valid())

    def test_empty_name_invalid(self) -> None:
        """空の名前が無効であることをテスト"""
        form = CategoryForm(data={'name': ''})
        self.assertFalse(form.is_valid())


class ExpensesViewTest(TestCase):
    """支出管理ビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='現金'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='食費'
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_expense_list_requires_login(self) -> None:
        """支出一覧に認証が必要であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 302)

    def test_expense_list_view(self) -> None:
        """支出一覧ビューのテスト"""
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/expenses/list.html')

    def test_expense_list_with_target_date(self) -> None:
        """対象月指定での支出一覧テスト"""
        response = self.client.get(reverse('expense_list'), {'target_date': '2024-01'})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_with_search(self) -> None:
        """検索機能のテスト"""
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='テスト用途',
            major_category='variable',
            category=self.category,
            purpose_description='テスト説明'
        )
        response = self.client.get(reverse('expense_list'), {'search': 'テスト'})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_filter_by_transaction_type(self) -> None:
        """取引タイプでのフィルタリングテスト"""
        response = self.client.get(reverse('expense_list'), {'transaction_type': 'expense'})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_filter_by_major_category(self) -> None:
        """大分類でのフィルタリングテスト"""
        response = self.client.get(reverse('expense_list'), {'major_category': 'variable'})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_filter_by_category(self) -> None:
        """カテゴリでのフィルタリングテスト"""
        response = self.client.get(reverse('expense_list'), {'category': self.category.id})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_filter_by_payment_method(self) -> None:
        """支払方法でのフィルタリングテスト"""
        response = self.client.get(reverse('expense_list'), {'payment_method': self.payment_method.id})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_pagination(self) -> None:
        """ページネーションのテスト"""
        for i in range(25):
            Transaction.objects.create(
                user=self.user,
                amount=Decimal('100.00'),
                date=timezone.now(),
                transaction_type='expense',
                payment_method=self.payment_method,
                purpose=f'取引{i}',
                major_category='variable',
                category=self.category,
                purpose_description='説明'
            )
        response = self.client.get(reverse('expense_list'), {'per_page': '10', 'page': '2'})
        self.assertEqual(response.status_code, 200)

    def test_expense_list_per_page_options(self) -> None:
        """ページあたり件数オプションのテスト"""
        for per_page in ['10', '20', '50', '100']:
            response = self.client.get(reverse('expense_list'), {'per_page': per_page})
            self.assertEqual(response.status_code, 200)

    def test_expense_list_invalid_per_page(self) -> None:
        """無効なページあたり件数のテスト（デフォルト20に戻る）"""
        response = self.client.get(reverse('expense_list'), {'per_page': '999'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['per_page'], 20)

    def test_create_expenses_view_get(self) -> None:
        """支出作成ビュー（GET）のテスト"""
        response = self.client.get(reverse('create_expenses'))
        self.assertEqual(response.status_code, 200)

    def test_create_expenses_view_post(self) -> None:
        """支出作成ビュー（POST）のテスト"""
        form_data = {
            'date': timezone.now().strftime('%Y-%m-%d'),
            'amount': 1000,
            'purpose': '昼食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
            'purpose_description': '説明',
        }
        response = self.client.post(reverse('create_expenses'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(purpose='昼食').exists())

    def test_edit_expenses_view_get(self) -> None:
        """支出編集ビュー（GET）のテスト"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='昼食',
            major_category='variable',
            category=self.category,
            purpose_description='説明'
        )
        response = self.client.get(reverse('edit_expenses', kwargs={'transaction_id': transaction.id}))
        self.assertEqual(response.status_code, 200)

    def test_edit_expenses_view_post(self) -> None:
        """支出編集ビュー（POST）のテスト"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='昼食',
            major_category='variable',
            category=self.category,
            purpose_description='説明'
        )
        form_data = {
            'date': timezone.now().strftime('%Y-%m-%d'),
            'amount': 2000,
            'purpose': '夕食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
            'purpose_description': '更新後説明',
        }
        response = self.client.post(
            reverse('edit_expenses', kwargs={'transaction_id': transaction.id}),
            form_data
        )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertEqual(transaction.purpose, '夕食')

    def test_edit_expenses_other_user_forbidden(self) -> None:
        """他ユーザーの支出編集が禁止されることをテスト"""
        User = get_user_model()
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            is_email_verified=True,
        )
        other_payment = PaymentMethod.objects.create(user=other_user, name='現金')
        other_category = Category.objects.create(user=other_user, name='食費')
        other_transaction = Transaction.objects.create(
            user=other_user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=other_payment,
            purpose='他ユーザー取引',
            major_category='variable',
            category=other_category,
            purpose_description='説明'
        )
        response = self.client.get(reverse('edit_expenses', kwargs={'transaction_id': other_transaction.id}))
        self.assertEqual(response.status_code, 404)

    def test_delete_expenses_view(self) -> None:
        """支出削除ビューのテスト"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='昼食',
            major_category='variable',
            category=self.category,
            purpose_description='説明'
        )
        response = self.client.post(reverse('delete_expenses', kwargs={'transaction_id': transaction.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())

    def test_expenses_settings_view(self) -> None:
        """設定ビューのテスト"""
        response = self.client.get(reverse('expenses_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/expenses/settings.html')

    def test_expenses_settings_add_payment_method(self) -> None:
        """支払方法追加のテスト"""
        initial_count = PaymentMethod.objects.filter(user=self.user).count()
        response = self.client.post(reverse('expenses_settings'), {
            'payment': '',
            'payment-name': 'クレジットカード'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PaymentMethod.objects.filter(user=self.user).count(), initial_count + 1)

    def test_expenses_settings_add_category(self) -> None:
        """カテゴリ追加のテスト"""
        initial_count = Category.objects.filter(user=self.user).count()
        response = self.client.post(reverse('expenses_settings'), {
            'purpose': '',
            'purpose-name': '交通費'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Category.objects.filter(user=self.user).count(), initial_count + 1)

    def test_expenses_settings_edit_payment_method(self) -> None:
        """支払方法編集のテスト"""
        response = self.client.post(reverse('expenses_settings'), {
            'payment_id': self.payment_method.id,
            'edit_payment': '',
            'payment-name': '更新済み'
        })
        self.assertEqual(response.status_code, 302)
        self.payment_method.refresh_from_db()
        self.assertEqual(self.payment_method.name, '更新済み')

    def test_expenses_settings_delete_payment_method(self) -> None:
        """支払方法削除のテスト"""
        payment_to_delete = PaymentMethod.objects.create(user=self.user, name='削除用')
        response = self.client.post(reverse('expenses_settings'), {
            'payment_id': payment_to_delete.id,
            'delete_payment': ''
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PaymentMethod.objects.filter(id=payment_to_delete.id).exists())

    def test_expenses_settings_payment_limit(self) -> None:
        """支払方法の上限テスト（10件まで）"""
        for i in range(9):  # 既存の1件と合わせて10件
            PaymentMethod.objects.create(user=self.user, name=f'支払方法{i}')

        response = self.client.post(reverse('expenses_settings'), {
            'payment': '',
            'payment-name': '新しい支払方法'
        })
        # 上限超過のためリダイレクトではなく同一ページ
        self.assertEqual(response.status_code, 200)

    def test_expenses_settings_category_limit(self) -> None:
        """カテゴリの上限テスト（10件まで）"""
        for i in range(9):  # 既存の1件と合わせて10件
            Category.objects.create(user=self.user, name=f'カテゴリ{i}')

        response = self.client.post(reverse('expenses_settings'), {
            'purpose': '',
            'purpose-name': '新しいカテゴリ'
        })
        self.assertEqual(response.status_code, 200)


class ExpensesAjaxViewTest(TestCase):
    """支出管理AJAXビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='現金'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='食費'
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_create_expenses_ajax_success(self) -> None:
        """AJAX経由での支出作成テスト（成功）"""
        form_data = {
            'date': timezone.now().strftime('%Y-%m-%d'),
            'amount': 1000,
            'purpose': '昼食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
            'purpose_description': '説明',
        }
        response = self.client.post(
            reverse('create_expenses'),
            form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))

    def test_create_expenses_ajax_invalid(self) -> None:
        """AJAX経由での無効な支出作成テスト"""
        form_data = {
            'date': '',
            'amount': -100,
            'purpose': '',
        }
        response = self.client.post(
            reverse('create_expenses'),
            form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get('success'))
        self.assertIn('errors', response.json())

    def test_edit_expenses_ajax_success(self) -> None:
        """AJAX経由での支出編集テスト（成功）"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='昼食',
            major_category='variable',
            category=self.category,
            purpose_description='説明'
        )
        form_data = {
            'date': timezone.now().strftime('%Y-%m-%d'),
            'amount': 2000,
            'purpose': '夕食',
            'transaction_type': 'expense',
            'major_category': 'variable',
            'category': self.category.id,
            'payment_method': self.payment_method.id,
            'purpose_description': '更新後説明',
        }
        response = self.client.post(
            reverse('edit_expenses', kwargs={'transaction_id': transaction.id}),
            form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))


class ExpensesChartDataTest(TestCase):
    """支出一覧のグラフデータテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            name='現金'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='食費'
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_chart_data_with_transactions(self) -> None:
        """取引がある場合のグラフデータテスト"""
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='昼食',
            major_category='variable',
            category=self.category,
            purpose_description='説明'
        )
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('category_data_json', response.context)
        self.assertIn('major_category_data_json', response.context)
        self.assertIn('expense_data_json', response.context)
        self.assertIn('balance_data_json', response.context)

    def test_chart_data_without_transactions(self) -> None:
        """取引がない場合のグラフデータテスト"""
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 200)
        # データがない場合は「データなし」のラベルが含まれる
        self.assertIn('データなし', response.context['category_data_json'])

    def test_summary_values(self) -> None:
        """合計値のテスト"""
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            date=timezone.now(),
            transaction_type='expense',
            payment_method=self.payment_method,
            purpose='支出1',
            major_category='variable',
            category=self.category,
            purpose_description='説明'
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            date=timezone.now(),
            transaction_type='income',
            payment_method=self.payment_method,
            purpose='収入1',
            major_category='fixed',
            category=self.category,
            purpose_description='説明'
        )
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_expense'], Decimal('1000.00'))
        self.assertEqual(response.context['total_income'], Decimal('5000.00'))
        self.assertEqual(response.context['net_balance'], 4000.0)
