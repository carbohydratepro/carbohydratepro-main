"""
選択モード＋一括削除エンドポイントのテスト
"""
import json

from django.test import Client, TestCase

from app.expenses.models import Transaction
from app.memo.models import Memo
from app.shopping.models import ShoppingItem
from tests.factories import (
    MemoFactory,
    ShoppingItemFactory,
    TransactionFactory,
    UserFactory,
)


class BulkDeleteMemoTest(TestCase):
    """メモの一括削除"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_bulk_delete_removes_selected(self) -> None:
        """選択したメモだけが削除され、件数が返る"""
        memos = [MemoFactory(user=self.user) for _ in range(3)]
        keep = MemoFactory(user=self.user)
        ids = [memos[0].id, memos[1].id, memos[2].id]

        response = self.client.post(
            '/carbohydratepro/memos/bulk-delete/',
            data=json.dumps({'ids': ids}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['deleted'], 3)
        self.assertTrue(Memo.objects.filter(id=keep.id).exists())
        self.assertEqual(Memo.objects.filter(id__in=ids).count(), 0)

    def test_cannot_delete_other_users_memos(self) -> None:
        """他ユーザーのメモは削除されない"""
        other = MemoFactory(user=UserFactory())
        response = self.client.post(
            '/carbohydratepro/memos/bulk-delete/',
            data=json.dumps({'ids': [other.id]}),
            content_type='application/json',
        )
        self.assertEqual(response.json()['deleted'], 0)
        self.assertTrue(Memo.objects.filter(id=other.id).exists())

    def test_get_is_not_allowed(self) -> None:
        """GET では削除できない"""
        response = self.client.get('/carbohydratepro/memos/bulk-delete/')
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self) -> None:
        """不正なJSONは400を返す"""
        response = self.client.post(
            '/carbohydratepro/memos/bulk-delete/',
            data='not-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_ids_deletes_nothing(self) -> None:
        """空リストは何も削除しない"""
        MemoFactory(user=self.user)
        response = self.client.post(
            '/carbohydratepro/memos/bulk-delete/',
            data=json.dumps({'ids': []}),
            content_type='application/json',
        )
        self.assertEqual(response.json()['deleted'], 0)

    def test_requires_login(self) -> None:
        """未ログインはログインへリダイレクトされる"""
        anon = Client()
        response = anon.post(
            '/carbohydratepro/memos/bulk-delete/',
            data=json.dumps({'ids': [1]}),
            content_type='application/json',
        )
        self.assertIn(response.status_code, (302, 403))


class BulkDeleteShoppingTest(TestCase):
    """買い物アイテムの一括削除"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_bulk_delete_shopping(self) -> None:
        items = [ShoppingItemFactory(user=self.user) for _ in range(2)]
        ids = [i.id for i in items]
        response = self.client.post(
            '/carbohydratepro/shopping/bulk-delete/',
            data=json.dumps({'ids': ids}),
            content_type='application/json',
        )
        self.assertEqual(response.json()['deleted'], 2)
        self.assertEqual(ShoppingItem.objects.filter(id__in=ids).count(), 0)


class BulkDeleteExpenseTest(TestCase):
    """取引の一括削除"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_bulk_delete_expenses(self) -> None:
        txns = [TransactionFactory(user=self.user) for _ in range(2)]
        other = TransactionFactory(user=UserFactory())
        ids = [t.id for t in txns] + [other.id]
        response = self.client.post(
            '/carbohydratepro/expenses/bulk-delete/',
            data=json.dumps({'ids': ids}),
            content_type='application/json',
        )
        # 自分の2件のみ削除、他人の1件は残る
        self.assertEqual(response.json()['deleted'], 2)
        self.assertTrue(Transaction.objects.filter(id=other.id).exists())
        self.assertEqual(Transaction.objects.filter(id__in=[t.id for t in txns]).count(), 0)
