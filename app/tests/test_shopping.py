from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.shopping.models import ShoppingItem
from app.shopping.forms import ShoppingItemForm


class ShoppingModelsTestCase(TestCase):
    """買い物リスト機能のモデルテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )

    def test_shopping_item_creation(self):
        """ShoppingItem モデルの作成テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="牛乳",
            frequency="recurring",
            price=Decimal("200.00"),
            remaining_count=5,
            threshold_count=2,
            memo="毎週購入"
        )
        
        self.assertEqual(str(item), "牛乳 - 残あり")
        self.assertEqual(item.status, "available")  # 5 > 2 なので残あり

    def test_shopping_item_status_insufficient(self):
        """ShoppingItem のステータス自動設定テスト（不足）"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="卵",
            frequency="recurring",
            remaining_count=1,
            threshold_count=3
        )
        
        self.assertEqual(item.status, "insufficient")  # 1 <= 3 なので不足

    def test_shopping_item_status_available(self):
        """ShoppingItem のステータス自動設定テスト（残あり）"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="パン",
            frequency="one_time",
            remaining_count=5,
            threshold_count=2
        )
        
        self.assertEqual(item.status, "available")  # 5 > 2 なので残あり

    def test_shopping_item_count_limit(self):
        """ShoppingItem の残数制限テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="お茶",
            frequency="recurring",
            remaining_count=1500,  # 999を超える
            threshold_count=-5  # 負の値
        )
        
        self.assertEqual(item.remaining_count, 999)  # 999に制限される
        self.assertEqual(item.threshold_count, 0)  # 0に制限される

    def test_shopping_item_ordering(self):
        """ShoppingItem の並び順テスト（不足→残あり、残数少ない順）"""
        item1 = ShoppingItem.objects.create(
            user=self.user,
            title="商品A",
            frequency="recurring",
            remaining_count=10,
            threshold_count=2
        )
        
        item2 = ShoppingItem.objects.create(
            user=self.user,
            title="商品B（不足）",
            frequency="recurring",
            remaining_count=1,
            threshold_count=3
        )
        
        item3 = ShoppingItem.objects.create(
            user=self.user,
            title="商品C（不足、より少ない）",
            frequency="one_time",
            remaining_count=0,
            threshold_count=2
        )
        
        items = ShoppingItem.objects.all()
        self.assertEqual(items[0], item3)  # 不足で残数最小
        self.assertEqual(items[1], item2)  # 不足
        self.assertEqual(items[2], item1)  # 残あり


class ShoppingFormsTestCase(TestCase):
    """買い物リスト機能のフォームテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )

    def test_shopping_item_form_valid(self):
        """ShoppingItemForm の正常なバリデーションテスト"""
        form = ShoppingItemForm(data={
            "title": "野菜",
            "frequency": "recurring",
            "price": "300.00",
            "remaining_count": 5,
            "threshold_count": 2,
            "memo": "新鮮なものを",
        })
        self.assertTrue(form.is_valid())

    def test_shopping_item_form_without_title(self):
        """ShoppingItemForm のタイトルなしのテスト"""
        form = ShoppingItemForm(data={
            "title": "",
            "frequency": "one_time",
            "remaining_count": 1,
            "threshold_count": 0,
        })
        self.assertFalse(form.is_valid())

    def test_shopping_item_form_negative_count(self):
        """ShoppingItemForm の負の残数テスト"""
        form = ShoppingItemForm(data={
            "title": "商品",
            "frequency": "recurring",
            "remaining_count": -5,
            "threshold_count": 2,
        })
        # フォームはバリデーションを通るが、モデル保存時に0に補正される
        self.assertTrue(form.is_valid())


class ShoppingViewsTestCase(TestCase):
    """買い物リスト機能のビューテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )
        self.client.login(username=self.user.email, password="testpass123")

    def test_shopping_list_view(self):
        """買い物リスト一覧ビューのテスト"""
        ShoppingItem.objects.create(
            user=self.user,
            title="テスト商品",
            frequency="recurring",
            remaining_count=3,
            threshold_count=1
        )
        
        response = self.client.get(reverse("shopping_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "テスト商品")

    def test_shopping_list_view_requires_login(self):
        """ログインしていない場合のアクセステスト"""
        self.client.logout()
        response = self.client.get(reverse("shopping_list"))
        self.assertEqual(response.status_code, 302)

    def test_create_shopping_item_view(self):
        """買い物アイテム作成ビューのテスト"""
        response = self.client.get(reverse("create_shopping_item"))
        self.assertEqual(response.status_code, 200)

    def test_create_shopping_item_post(self):
        """買い物アイテム作成POSTリクエストのテスト"""
        data = {
            "title": "新商品",
            "frequency": "one_time",
            "price": "500.00",
            "remaining_count": 2,
            "threshold_count": 1,
            "memo": "テストメモ",
        }
        response = self.client.post(reverse("create_shopping_item"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ShoppingItem.objects.filter(title="新商品").exists())

    def test_update_shopping_item_view(self):
        """買い物アイテム更新ビューのテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="更新テスト",
            frequency="recurring",
            remaining_count=5,
            threshold_count=2
        )
        
        response = self.client.get(reverse("update_shopping_item", args=[item.id]))
        self.assertEqual(response.status_code, 200)

    def test_delete_shopping_item(self):
        """買い物アイテム削除のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="削除テスト",
            frequency="one_time",
            remaining_count=1,
            threshold_count=0
        )
        
        response = self.client.post(reverse("delete_shopping_item", args=[item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ShoppingItem.objects.filter(id=item.id).exists())

    def test_increment_shopping_item(self):
        """買い物アイテム残数増加のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="増加テスト",
            frequency="recurring",
            remaining_count=5,
            threshold_count=2
        )
        
        response = self.client.post(reverse("increment_shopping_item", args=[item.id]))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 6)

    def test_decrement_shopping_item(self):
        """買い物アイテム残数減少のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="減少テスト",
            frequency="recurring",
            remaining_count=5,
            threshold_count=2
        )
        
        response = self.client.post(reverse("decrement_shopping_item", args=[item.id]))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 4)

    def test_decrement_shopping_item_min_zero(self):
        """買い物アイテム残数減少の下限テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title="下限テスト",
            frequency="one_time",
            remaining_count=0,
            threshold_count=1
        )
        
        response = self.client.post(reverse("decrement_shopping_item", args=[item.id]))
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 0)  # 0以下にならない
