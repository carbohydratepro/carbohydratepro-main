from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.memo.models import Memo, MemoType
from app.memo.forms import MemoForm, MemoTypeForm


class MemoModelsTestCase(TestCase):
    """メモ機能のモデルテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )

    def test_memo_type_creation(self):
        """MemoType モデルの作成テスト"""
        memo_type = MemoType.objects.create(
            user=self.user,
            name="仕事",
            color="#FF5733"
        )
        self.assertEqual(str(memo_type), "仕事")
        self.assertEqual(memo_type.color, "#FF5733")

    def test_memo_type_unique_constraint(self):
        """MemoType のユニーク制約テスト"""
        MemoType.objects.create(user=self.user, name="仕事")
        
        # 同じユーザーと名前の組み合わせは作成できない
        with self.assertRaises(Exception):
            MemoType.objects.create(user=self.user, name="仕事")

    def test_memo_creation(self):
        """Memo モデルの作成テスト"""
        memo_type = MemoType.objects.create(user=self.user, name="個人")
        memo = Memo.objects.create(
            user=self.user,
            title="買い物リスト",
            memo_type=memo_type,
            content="牛乳、卵、パン",
            is_favorite=False
        )
        
        self.assertEqual(str(memo), "買い物リスト - 個人")
        self.assertFalse(memo.is_favorite)
        self.assertEqual(memo.content, "牛乳、卵、パン")

    def test_memo_favorite(self):
        """Memo のお気に入り機能テスト"""
        memo_type = MemoType.objects.create(user=self.user, name="重要")
        memo = Memo.objects.create(
            user=self.user,
            title="重要なメモ",
            memo_type=memo_type,
            is_favorite=True
        )
        
        self.assertTrue(memo.is_favorite)

    def test_memo_ordering(self):
        """Memo の並び順テスト（お気に入り優先、更新日降順）"""
        memo_type = MemoType.objects.create(user=self.user, name="テスト")
        
        memo1 = Memo.objects.create(
            user=self.user,
            title="通常メモ1",
            memo_type=memo_type,
            is_favorite=False
        )
        
        memo2 = Memo.objects.create(
            user=self.user,
            title="お気に入りメモ",
            memo_type=memo_type,
            is_favorite=True
        )
        
        memos = Memo.objects.all()
        self.assertEqual(memos[0], memo2)  # お気に入りが最初
        self.assertEqual(memos[1], memo1)


class MemoFormsTestCase(TestCase):
    """メモ機能のフォームテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )
        self.memo_type = MemoType.objects.create(user=self.user, name="一般")

    def test_memo_form_valid(self):
        """MemoForm の正常なバリデーションテスト"""
        form = MemoForm(
            user=self.user,
            data={
                "title": "テストメモ",
                "memo_type": self.memo_type.id,
                "content": "これはテストです",
                "is_favorite": False,
            }
        )
        self.assertTrue(form.is_valid())

    def test_memo_form_without_title(self):
        """MemoForm のタイトルなしのテスト"""
        form = MemoForm(
            user=self.user,
            data={
                "title": "",  # タイトルなし
                "memo_type": self.memo_type.id,
                "content": "内容あり",
                "is_favorite": False,
            }
        )
        self.assertFalse(form.is_valid())

    def test_memo_type_form_valid(self):
        """MemoTypeForm の正常なバリデーションテスト"""
        form = MemoTypeForm(data={
            "name": "プライベート",
            "color": "#00FF00"
        })
        self.assertTrue(form.is_valid())


class MemoViewsTestCase(TestCase):
    """メモ機能のビューテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )
        self.client.login(username=self.user.email, password="testpass123")
        
        self.memo_type = MemoType.objects.create(user=self.user, name="テスト")

    def test_memo_list_view(self):
        """メモ一覧ビューのテスト"""
        Memo.objects.create(
            user=self.user,
            title="テストメモ",
            memo_type=self.memo_type,
            content="テスト内容"
        )
        
        response = self.client.get(reverse("memo_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "テストメモ")

    def test_memo_list_view_requires_login(self):
        """ログインしていない場合のアクセステスト"""
        self.client.logout()
        response = self.client.get(reverse("memo_list"))
        self.assertEqual(response.status_code, 302)

    def test_create_memo_view(self):
        """メモ作成ビューのテスト"""
        response = self.client.get(reverse("create_memo"))
        self.assertEqual(response.status_code, 200)

    def test_create_memo_post(self):
        """メモ作成POSTリクエストのテスト"""
        data = {
            "title": "新しいメモ",
            "memo_type": self.memo_type.id,
            "content": "新しい内容",
            "is_favorite": True,
        }
        response = self.client.post(reverse("create_memo"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Memo.objects.filter(title="新しいメモ").exists())
        
        memo = Memo.objects.get(title="新しいメモ")
        self.assertTrue(memo.is_favorite)

    def test_update_memo_view(self):
        """メモ更新ビューのテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title="更新前",
            memo_type=self.memo_type,
            content="更新前の内容"
        )
        
        response = self.client.get(reverse("update_memo", args=[memo.id]))
        self.assertEqual(response.status_code, 200)

    def test_delete_memo(self):
        """メモ削除のテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title="削除テスト",
            memo_type=self.memo_type,
            content="削除される"
        )
        
        response = self.client.post(reverse("delete_memo", args=[memo.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Memo.objects.filter(id=memo.id).exists())

    def test_memo_type_list_view(self):
        """メモ種別一覧ビューのテスト"""
        response = self.client.get(reverse("memo_type_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "テスト")

    def test_toggle_favorite(self):
        """お気に入り切り替えのテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title="お気に入りテスト",
            memo_type=self.memo_type,
            is_favorite=False
        )
        
        # お気に入りに追加
        response = self.client.post(reverse("toggle_memo_favorite", args=[memo.id]))
        self.assertEqual(response.status_code, 302)
        memo.refresh_from_db()
        self.assertTrue(memo.is_favorite)
        
        # お気に入りから削除
        response = self.client.post(reverse("toggle_memo_favorite", args=[memo.id]))
        memo.refresh_from_db()
        self.assertFalse(memo.is_favorite)
