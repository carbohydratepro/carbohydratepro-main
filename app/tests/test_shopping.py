"""
買い物リスト機能のテスト
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from app.shopping.models import ShoppingItem
from app.shopping.forms import ShoppingItemForm


class ShoppingItemModelTest(TestCase):
    """買い物アイテムモデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )

    def test_create_shopping_item(self) -> None:
        """買い物アイテムの作成テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='牛乳',
            frequency='recurring',
            price=Decimal('200.00'),
            remaining_count=5,
            threshold_count=2,
            memo='毎週購入'
        )
        self.assertEqual(str(item), '牛乳 - 残あり')
        self.assertEqual(item.status, 'available')

    def test_status_auto_set_insufficient(self) -> None:
        """ステータス自動設定テスト（不足）"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='卵',
            frequency='recurring',
            remaining_count=1,
            threshold_count=3
        )
        self.assertEqual(item.status, 'insufficient')

    def test_status_auto_set_available(self) -> None:
        """ステータス自動設定テスト（残あり）"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='パン',
            frequency='one_time',
            remaining_count=5,
            threshold_count=2
        )
        self.assertEqual(item.status, 'available')

    def test_status_equal_threshold(self) -> None:
        """残数と閾値が等しい場合のステータステスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='バター',
            frequency='recurring',
            remaining_count=3,
            threshold_count=3
        )
        self.assertEqual(item.status, 'insufficient')

    def test_count_max_limit(self) -> None:
        """残数の上限制限テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='お茶',
            frequency='recurring',
            remaining_count=1500,
            threshold_count=0
        )
        self.assertEqual(item.remaining_count, 999)

    def test_count_min_limit(self) -> None:
        """残数の下限制限テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='ジュース',
            frequency='recurring',
            remaining_count=-5,
            threshold_count=-10
        )
        self.assertEqual(item.remaining_count, 0)
        self.assertEqual(item.threshold_count, 0)

    def test_ordering(self) -> None:
        """買い物アイテムの並び順テスト（ステータス順、残数少ない順）"""
        item1 = ShoppingItem.objects.create(
            user=self.user,
            title='商品A',
            frequency='recurring',
            remaining_count=10,
            threshold_count=2
        )
        item2 = ShoppingItem.objects.create(
            user=self.user,
            title='商品B（不足）',
            frequency='recurring',
            remaining_count=1,
            threshold_count=3
        )
        item3 = ShoppingItem.objects.create(
            user=self.user,
            title='商品C（不足、より少ない）',
            frequency='one_time',
            remaining_count=0,
            threshold_count=2
        )
        items = ShoppingItem.objects.filter(user=self.user)
        # ordering は ['status', 'remaining_count', '-updated_date']
        # status のアルファベット順: 'available' < 'insufficient'
        # item1: available, remaining_count=10
        # item2: insufficient, remaining_count=1
        # item3: insufficient, remaining_count=0
        self.assertEqual(items[0], item1)  # available が先
        self.assertEqual(items[1], item3)  # insufficient, remaining_count=0
        self.assertEqual(items[2], item2)  # insufficient, remaining_count=1

    def test_frequency_choices(self) -> None:
        """頻度の選択肢テスト"""
        choices = dict(ShoppingItem.FREQUENCY_CHOICES)
        self.assertIn('one_time', choices)
        self.assertIn('recurring', choices)

    def test_status_choices(self) -> None:
        """ステータスの選択肢テスト"""
        choices = dict(ShoppingItem.STATUS_CHOICES)
        self.assertIn('insufficient', choices)
        self.assertIn('available', choices)

    def test_auto_timestamps(self) -> None:
        """タイムスタンプ自動設定テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='タイムスタンプテスト',
            frequency='one_time'
        )
        self.assertIsNotNone(item.created_date)
        self.assertIsNotNone(item.updated_date)


class ShoppingItemFormTest(TestCase):
    """買い物アイテムフォームのテスト"""

    def test_valid_form(self) -> None:
        """有効なフォームのテスト"""
        form = ShoppingItemForm(data={
            'title': '野菜',
            'frequency': 'recurring',
            'price': '300.00',
            'remaining_count': 5,
            'threshold_count': 2,
            'memo': '新鮮なものを',
        })
        self.assertTrue(form.is_valid())

    def test_form_without_title_invalid(self) -> None:
        """タイトルなしのフォームが無効であることをテスト"""
        form = ShoppingItemForm(data={
            'title': '',
            'frequency': 'one_time',
            'remaining_count': 1,
            'threshold_count': 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_without_frequency_invalid(self) -> None:
        """頻度なしのフォームが無効であることをテスト"""
        form = ShoppingItemForm(data={
            'title': '商品',
            'frequency': '',
            'remaining_count': 1,
            'threshold_count': 0,
        })
        self.assertFalse(form.is_valid())

    def test_form_with_optional_price(self) -> None:
        """金額なしでもフォームが有効であることをテスト"""
        form = ShoppingItemForm(data={
            'title': '商品',
            'frequency': 'recurring',
            'remaining_count': 1,
            'threshold_count': 0,
        })
        self.assertTrue(form.is_valid())


class ShoppingViewTest(TestCase):
    """買い物リストビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_shopping_list_requires_login(self) -> None:
        """買い物リスト一覧に認証が必要であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse('shopping_list'))
        self.assertEqual(response.status_code, 302)

    def test_shopping_list_view(self) -> None:
        """買い物リスト一覧ビューのテスト"""
        ShoppingItem.objects.create(
            user=self.user,
            title='テスト商品',
            frequency='recurring',
            remaining_count=3,
            threshold_count=1
        )
        response = self.client.get(reverse('shopping_list'))
        self.assertEqual(response.status_code, 200)

    def test_shopping_list_with_search(self) -> None:
        """検索機能のテスト"""
        ShoppingItem.objects.create(
            user=self.user,
            title='検索対象商品',
            frequency='recurring',
            remaining_count=3,
            threshold_count=1
        )
        response = self.client.get(reverse('shopping_list'), {'search': '検索対象'})
        self.assertEqual(response.status_code, 200)

    def test_shopping_list_filter_by_status(self) -> None:
        """ステータスでのフィルタリングテスト"""
        response = self.client.get(reverse('shopping_list'), {'status': 'insufficient'})
        self.assertEqual(response.status_code, 200)

    def test_shopping_list_filter_by_frequency(self) -> None:
        """頻度でのフィルタリングテスト"""
        response = self.client.get(reverse('shopping_list'), {'frequency': 'recurring'})
        self.assertEqual(response.status_code, 200)

    def test_create_shopping_item_view_get(self) -> None:
        """買い物アイテム作成ビュー（GET）のテスト"""
        response = self.client.get(reverse('create_shopping_item'))
        self.assertEqual(response.status_code, 200)

    def test_create_shopping_item_view_post(self) -> None:
        """買い物アイテム作成ビュー（POST）のテスト"""
        data = {
            'title': '新商品',
            'frequency': 'one_time',
            'price': '500.00',
            'remaining_count': 2,
            'threshold_count': 1,
            'memo': 'テストメモ',
        }
        response = self.client.post(reverse('create_shopping_item'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ShoppingItem.objects.filter(title='新商品').exists())

    def test_edit_shopping_item_view_get(self) -> None:
        """買い物アイテム編集ビュー（GET）のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='編集テスト',
            frequency='recurring',
            remaining_count=5,
            threshold_count=2
        )
        response = self.client.get(reverse('edit_shopping_item', kwargs={'item_id': item.id}))
        self.assertEqual(response.status_code, 200)

    def test_edit_shopping_item_view_post(self) -> None:
        """買い物アイテム編集ビュー（POST）のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='編集テスト',
            frequency='recurring',
            remaining_count=5,
            threshold_count=2
        )
        data = {
            'title': '編集後商品',
            'frequency': 'one_time',
            'remaining_count': 3,
            'threshold_count': 1,
            'memo': '編集後メモ',
        }
        response = self.client.post(reverse('edit_shopping_item', kwargs={'item_id': item.id}), data)
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.title, '編集後商品')

    def test_edit_shopping_item_other_user_forbidden(self) -> None:
        """他ユーザーの買い物アイテム編集が禁止されることをテスト"""
        User = get_user_model()
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            is_email_verified=True,
        )
        other_item = ShoppingItem.objects.create(
            user=other_user,
            title='他ユーザー商品',
            frequency='recurring',
            remaining_count=3,
            threshold_count=1
        )
        response = self.client.get(reverse('edit_shopping_item', kwargs={'item_id': other_item.id}))
        self.assertEqual(response.status_code, 404)

    def test_delete_shopping_item_view(self) -> None:
        """買い物アイテム削除ビューのテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='削除テスト',
            frequency='one_time',
            remaining_count=1,
            threshold_count=0
        )
        response = self.client.post(reverse('delete_shopping_item', kwargs={'item_id': item.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ShoppingItem.objects.filter(id=item.id).exists())

    def test_update_shopping_count_increment(self) -> None:
        """残数増加のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='増加テスト',
            frequency='recurring',
            remaining_count=5,
            threshold_count=2
        )
        response = self.client.post(
            reverse('update_shopping_count', kwargs={'item_id': item.id}),
            {'field_type': 'remaining', 'action': 'increase'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 6)

    def test_update_shopping_count_decrement(self) -> None:
        """残数減少のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='減少テスト',
            frequency='recurring',
            remaining_count=5,
            threshold_count=2
        )
        response = self.client.post(
            reverse('update_shopping_count', kwargs={'item_id': item.id}),
            {'field_type': 'remaining', 'action': 'decrease'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 4)

    def test_update_shopping_count_decrement_min_zero(self) -> None:
        """残数減少の下限テスト（0以下にならない）"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='下限テスト',
            frequency='one_time',
            remaining_count=0,
            threshold_count=1
        )
        response = self.client.post(
            reverse('update_shopping_count', kwargs={'item_id': item.id}),
            {'field_type': 'remaining', 'action': 'decrease'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 0)

    def test_update_shopping_count_status_change(self) -> None:
        """残数変更でステータスが変わることをテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='ステータス変更テスト',
            frequency='recurring',
            remaining_count=3,
            threshold_count=2
        )
        self.assertEqual(item.status, 'available')

        # 残数を減らして閾値以下に
        response = self.client.post(
            reverse('update_shopping_count', kwargs={'item_id': item.id}),
            {'field_type': 'remaining', 'action': 'decrease'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 2)
        self.assertEqual(item.status, 'insufficient')


class ShoppingAjaxViewTest(TestCase):
    """買い物リストAJAXビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_create_shopping_item_ajax_success(self) -> None:
        """AJAX経由での買い物アイテム作成テスト（成功）"""
        data = {
            'title': 'AJAX商品',
            'frequency': 'recurring',
            'remaining_count': 5,
            'threshold_count': 2,
        }
        response = self.client.post(
            reverse('create_shopping_item'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))

    def test_update_shopping_count_ajax(self) -> None:
        """AJAX経由での残数更新テスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='AJAX更新テスト',
            frequency='recurring',
            remaining_count=5,
            threshold_count=2
        )
        response = self.client.post(
            reverse('update_shopping_count', kwargs={'item_id': item.id}),
            {'field_type': 'remaining', 'action': 'increase'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 6)
