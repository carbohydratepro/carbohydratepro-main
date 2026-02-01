from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.expenses.models import Category, PaymentMethod, Transaction
from app.expenses.forms import TransactionForm, PaymentMethodForm, CategoryForm


class ExpensesModelsTestCase(TestCase):
    """家計簿機能のモデルテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )

    def test_payment_method_creation(self):
        """PaymentMethod モデルの作成テスト"""
        payment = PaymentMethod.objects.create(
            user=self.user,
            name="クレジットカード"
        )
        self.assertEqual(str(payment), "クレジットカード")
        self.assertEqual(payment.user, self.user)

    def test_category_creation(self):
        """Category モデルの作成テスト"""
        category = Category.objects.create(
            user=self.user,
            name="食費"
        )
        self.assertEqual(str(category), "食費")
        self.assertEqual(category.user, self.user)

    def test_transaction_creation(self):
        """Transaction モデルの作成テスト"""
        payment = PaymentMethod.objects.create(user=self.user, name="現金")
        category = Category.objects.create(user=self.user, name="食費")
        
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal("1500.00"),
            date=timezone.now(),
            transaction_type="expense",
            payment_method=payment,
            purpose="ランチ",
            major_category="variable",
            category=category,
            purpose_description="コンビニで弁当購入"
        )
        
        self.assertEqual(transaction.amount, Decimal("1500.00"))
        self.assertEqual(transaction.transaction_type, "expense")
        self.assertEqual(transaction.payment_method, payment)
        self.assertEqual(transaction.category, category)
        self.assertIn(self.user.email, str(transaction))


class ExpensesFormsTestCase(TestCase):
    """家計簿機能のフォームテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )
        self.payment = PaymentMethod.objects.create(user=self.user, name="現金")
        self.category = Category.objects.create(user=self.user, name="食費")

    def test_transaction_form_valid(self):
        """TransactionForm の正常なバリデーションテスト"""
        form = TransactionForm(
            user=self.user,
            data={
                "amount": "1000.00",
                "date": timezone.now(),
                "transaction_type": "expense",
                "payment_method": self.payment.id,
                "purpose": "買い物",
                "major_category": "variable",
                "category": self.category.id,
                "purpose_description": "スーパーで買い物",
            }
        )
        self.assertTrue(form.is_valid())

    def test_transaction_form_invalid_amount(self):
        """TransactionForm の金額が不正な場合のテスト"""
        form = TransactionForm(
            user=self.user,
            data={
                "amount": "-100.00",  # 負の金額
                "date": timezone.now(),
                "transaction_type": "expense",
                "payment_method": self.payment.id,
                "purpose": "買い物",
                "major_category": "variable",
                "category": self.category.id,
                "purpose_description": "テスト",
            }
        )
        self.assertFalse(form.is_valid())

    def test_payment_method_form_valid(self):
        """PaymentMethodForm の正常なバリデーションテスト"""
        form = PaymentMethodForm(data={"name": "銀行振込"})
        self.assertTrue(form.is_valid())

    def test_category_form_valid(self):
        """CategoryForm の正常なバリデーションテスト"""
        form = CategoryForm(data={"name": "交通費"})
        self.assertTrue(form.is_valid())


class ExpensesViewsTestCase(TestCase):
    """家計簿機能のビューテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )
        self.client.login(username=self.user.email, password="testpass123")
        
        self.payment = PaymentMethod.objects.create(user=self.user, name="現金")
        self.category = Category.objects.create(user=self.user, name="食費")

    def test_expenses_list_view(self):
        """家計簿一覧ビューのテスト"""
        Transaction.objects.create(
            user=self.user,
            amount=Decimal("1500.00"),
            date=timezone.now(),
            transaction_type="expense",
            payment_method=self.payment,
            purpose="ランチ",
            major_category="variable",
            category=self.category,
            purpose_description="テスト"
        )
        
        response = self.client.get(reverse("expenses_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ランチ")

    def test_expenses_list_view_requires_login(self):
        """ログインしていない場合のアクセステスト"""
        self.client.logout()
        response = self.client.get(reverse("expenses_list"))
        self.assertEqual(response.status_code, 302)  # ログインページへリダイレクト

    def test_create_transaction_view(self):
        """取引作成ビューのテスト"""
        response = self.client.get(reverse("create_expenses"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "金額")

    def test_create_transaction_post(self):
        """取引作成POSTリクエストのテスト"""
        data = {
            "amount": "2000.00",
            "date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": "expense",
            "payment_method": self.payment.id,
            "purpose": "ディナー",
            "major_category": "variable",
            "category": self.category.id,
            "purpose_description": "レストランで食事",
        }
        response = self.client.post(reverse("create_expenses"), data)
        self.assertEqual(response.status_code, 302)  # リダイレクト
        self.assertTrue(Transaction.objects.filter(purpose="ディナー").exists())

    def test_payment_method_list_view(self):
        """支払い方法一覧ビューのテスト"""
        response = self.client.get(reverse("payment_method_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "現金")

    def test_category_list_view(self):
        """カテゴリ一覧ビューのテスト"""
        response = self.client.get(reverse("category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "食費")

    def test_delete_transaction(self):
        """取引削除のテスト"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal("1000.00"),
            date=timezone.now(),
            transaction_type="expense",
            payment_method=self.payment,
            purpose="テスト削除",
            major_category="variable",
            category=self.category,
            purpose_description="削除テスト"
        )
        
        response = self.client.post(reverse("delete_expenses", args=[transaction.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())
