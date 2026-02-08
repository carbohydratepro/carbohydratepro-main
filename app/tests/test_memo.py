"""
メモ機能のテスト
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from app.memo.models import Memo, MemoType
from app.memo.forms import MemoForm, MemoTypeForm


class MemoTypeModelTest(TestCase):
    """メモ種別モデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )

    def test_create_memo_type(self) -> None:
        """メモ種別の作成テスト"""
        memo_type = MemoType.objects.create(
            user=self.user,
            name='仕事',
            color='#FF5733'
        )
        self.assertEqual(str(memo_type), '仕事')
        self.assertEqual(memo_type.color, '#FF5733')

    def test_memo_type_default_color(self) -> None:
        """デフォルト色のテスト"""
        memo_type = MemoType.objects.create(
            user=self.user,
            name='テスト'
        )
        self.assertEqual(memo_type.color, '#6c757d')

    def test_memo_type_unique_constraint(self) -> None:
        """メモ種別のユニーク制約テスト"""
        MemoType.objects.create(user=self.user, name='仕事')
        with self.assertRaises(Exception):
            MemoType.objects.create(user=self.user, name='仕事')

    def test_global_memo_type(self) -> None:
        """共通メモ種別（user=None）のテスト"""
        global_type = MemoType.objects.create(
            user=None,
            name='メモ'
        )
        self.assertIsNone(global_type.user)

    def test_memo_type_ordering(self) -> None:
        """メモ種別の並び順テスト（名前順）"""
        MemoType.objects.create(user=self.user, name='Zカテゴリ')
        MemoType.objects.create(user=self.user, name='Aカテゴリ')
        types = MemoType.objects.filter(user=self.user)
        self.assertEqual(types[0].name, 'Aカテゴリ')


class MemoModelTest(TestCase):
    """メモモデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.memo_type = MemoType.objects.create(user=self.user, name='個人')

    def test_create_memo(self) -> None:
        """メモの作成テスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='買い物リスト',
            memo_type=self.memo_type,
            content='牛乳、卵、パン',
            is_favorite=False
        )
        self.assertEqual(str(memo), '買い物リスト - 個人')
        self.assertFalse(memo.is_favorite)
        self.assertEqual(memo.content, '牛乳、卵、パン')

    def test_create_favorite_memo(self) -> None:
        """お気に入りメモの作成テスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='重要なメモ',
            memo_type=self.memo_type,
            is_favorite=True
        )
        self.assertTrue(memo.is_favorite)

    def test_memo_ordering(self) -> None:
        """メモの並び順テスト（お気に入り優先、更新日降順）"""
        memo1 = Memo.objects.create(
            user=self.user,
            title='通常メモ1',
            memo_type=self.memo_type,
            is_favorite=False
        )
        memo2 = Memo.objects.create(
            user=self.user,
            title='お気に入りメモ',
            memo_type=self.memo_type,
            is_favorite=True
        )
        memos = Memo.objects.filter(user=self.user)
        self.assertEqual(memos[0], memo2)
        self.assertEqual(memos[1], memo1)

    def test_memo_auto_timestamps(self) -> None:
        """メモのタイムスタンプ自動設定テスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='タイムスタンプテスト',
            memo_type=self.memo_type
        )
        self.assertIsNotNone(memo.created_date)
        self.assertIsNotNone(memo.updated_date)


class MemoFormTest(TestCase):
    """メモフォームのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.memo_type = MemoType.objects.create(user=self.user, name='一般')

    def test_valid_form(self) -> None:
        """有効なフォームのテスト"""
        form = MemoForm(
            user=self.user,
            data={
                'title': 'テストメモ',
                'memo_type': self.memo_type.id,
                'content': 'これはテストです',
                'is_favorite': False,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_without_title_invalid(self) -> None:
        """タイトルなしのフォームが無効であることをテスト"""
        form = MemoForm(
            user=self.user,
            data={
                'title': '',
                'memo_type': self.memo_type.id,
                'content': '内容あり',
                'is_favorite': False,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_filters_memo_types_by_user(self) -> None:
        """フォームがユーザーのメモ種別のみを表示することをテスト"""
        User = get_user_model()
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            is_email_verified=True,
        )
        other_type = MemoType.objects.create(user=other_user, name='他ユーザー種別')

        form = MemoForm(user=self.user)
        queryset = form.fields['memo_type'].queryset
        self.assertNotIn(other_type, queryset)


class MemoTypeFormTest(TestCase):
    """メモ種別フォームのテスト"""

    def test_valid_form(self) -> None:
        """有効なフォームのテスト"""
        form = MemoTypeForm(data={
            'name': 'プライベート',
            'color': '#00FF00'
        })
        self.assertTrue(form.is_valid())

    def test_form_without_name_invalid(self) -> None:
        """名前なしのフォームが無効であることをテスト"""
        form = MemoTypeForm(data={
            'name': '',
            'color': '#00FF00'
        })
        self.assertFalse(form.is_valid())


class MemoViewTest(TestCase):
    """メモビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.memo_type = MemoType.objects.create(user=self.user, name='テスト')
        self.client.login(username='test@example.com', password='testpass123')

    def test_memo_list_requires_login(self) -> None:
        """メモ一覧に認証が必要であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse('memo_list'))
        self.assertEqual(response.status_code, 302)

    def test_memo_list_view(self) -> None:
        """メモ一覧ビューのテスト"""
        Memo.objects.create(
            user=self.user,
            title='テストメモ',
            memo_type=self.memo_type,
            content='テスト内容'
        )
        response = self.client.get(reverse('memo_list'))
        self.assertEqual(response.status_code, 200)

    def test_memo_list_with_search(self) -> None:
        """検索機能のテスト"""
        Memo.objects.create(
            user=self.user,
            title='検索対象メモ',
            memo_type=self.memo_type,
            content='検索用コンテンツ'
        )
        response = self.client.get(reverse('memo_list'), {'search': '検索対象'})
        self.assertEqual(response.status_code, 200)

    def test_memo_list_filter_by_type(self) -> None:
        """メモ種別でのフィルタリングテスト"""
        response = self.client.get(reverse('memo_list'), {'memo_type': self.memo_type.id})
        self.assertEqual(response.status_code, 200)

    def test_memo_list_filter_by_favorite(self) -> None:
        """お気に入りでのフィルタリングテスト"""
        response = self.client.get(reverse('memo_list'), {'is_favorite': 'true'})
        self.assertEqual(response.status_code, 200)

    def test_create_memo_view_get(self) -> None:
        """メモ作成ビュー（GET）のテスト"""
        response = self.client.get(reverse('create_memo'))
        self.assertEqual(response.status_code, 200)

    def test_create_memo_view_post(self) -> None:
        """メモ作成ビュー（POST）のテスト"""
        data = {
            'title': '新しいメモ',
            'memo_type': self.memo_type.id,
            'content': '新しい内容',
            'is_favorite': True,
        }
        response = self.client.post(reverse('create_memo'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Memo.objects.filter(title='新しいメモ').exists())
        memo = Memo.objects.get(title='新しいメモ')
        self.assertTrue(memo.is_favorite)

    def test_edit_memo_view_get(self) -> None:
        """メモ編集ビュー（GET）のテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='編集テスト',
            memo_type=self.memo_type,
            content='編集前の内容'
        )
        response = self.client.get(reverse('edit_memo', kwargs={'memo_id': memo.id}))
        self.assertEqual(response.status_code, 200)

    def test_edit_memo_view_post(self) -> None:
        """メモ編集ビュー（POST）のテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='編集テスト',
            memo_type=self.memo_type,
            content='編集前の内容'
        )
        data = {
            'title': '編集後のメモ',
            'memo_type': self.memo_type.id,
            'content': '編集後の内容',
            'is_favorite': False,
        }
        response = self.client.post(reverse('edit_memo', kwargs={'memo_id': memo.id}), data)
        self.assertEqual(response.status_code, 302)
        memo.refresh_from_db()
        self.assertEqual(memo.title, '編集後のメモ')

    def test_edit_memo_other_user_forbidden(self) -> None:
        """他ユーザーのメモ編集が禁止されることをテスト"""
        User = get_user_model()
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            is_email_verified=True,
        )
        other_type = MemoType.objects.create(user=other_user, name='他ユーザー')
        other_memo = Memo.objects.create(
            user=other_user,
            title='他ユーザーメモ',
            memo_type=other_type
        )
        response = self.client.get(reverse('edit_memo', kwargs={'memo_id': other_memo.id}))
        self.assertEqual(response.status_code, 404)

    def test_delete_memo_view(self) -> None:
        """メモ削除ビューのテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='削除テスト',
            memo_type=self.memo_type,
            content='削除される'
        )
        response = self.client.post(reverse('delete_memo', kwargs={'memo_id': memo.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Memo.objects.filter(id=memo.id).exists())

    def test_toggle_memo_favorite(self) -> None:
        """お気に入り切り替えのテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='お気に入りテスト',
            memo_type=self.memo_type,
            is_favorite=False
        )
        # お気に入りに追加（JSONレスポンスを返す）
        response = self.client.post(reverse('toggle_memo_favorite', kwargs={'memo_id': memo.id}))
        self.assertEqual(response.status_code, 200)
        memo.refresh_from_db()
        self.assertTrue(memo.is_favorite)

        # お気に入りから削除
        response = self.client.post(reverse('toggle_memo_favorite', kwargs={'memo_id': memo.id}))
        self.assertEqual(response.status_code, 200)
        memo.refresh_from_db()
        self.assertFalse(memo.is_favorite)

    def test_memo_settings_view(self) -> None:
        """メモ設定ビューのテスト"""
        response = self.client.get(reverse('memo_settings'))
        self.assertEqual(response.status_code, 200)

    def test_memo_settings_add_type(self) -> None:
        """メモ種別追加のテスト"""
        initial_count = MemoType.objects.filter(user=self.user).count()
        response = self.client.post(reverse('memo_settings'), {
            'create_memo_type': '',
            'name': '新しい種別',
            'color': '#FF0000'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MemoType.objects.filter(user=self.user).count(), initial_count + 1)

    def test_memo_settings_delete_type(self) -> None:
        """メモ種別削除のテスト"""
        type_to_delete = MemoType.objects.create(user=self.user, name='削除用')
        response = self.client.post(reverse('memo_settings'), {
            'memo_type_id': type_to_delete.id,
            'delete_memo_type': ''
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MemoType.objects.filter(id=type_to_delete.id).exists())


class MemoAjaxViewTest(TestCase):
    """メモAJAXビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.memo_type = MemoType.objects.create(user=self.user, name='テスト')
        self.client.login(username='test@example.com', password='testpass123')

    def test_create_memo_ajax_success(self) -> None:
        """AJAX経由でのメモ作成テスト（成功）"""
        data = {
            'title': 'AJAXメモ',
            'memo_type': self.memo_type.id,
            'content': 'AJAX内容',
            'is_favorite': False,
        }
        response = self.client.post(
            reverse('create_memo'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))

    def test_toggle_favorite_ajax(self) -> None:
        """AJAX経由でのお気に入り切り替えテスト"""
        memo = Memo.objects.create(
            user=self.user,
            title='AJAX切り替えテスト',
            memo_type=self.memo_type,
            is_favorite=False
        )
        response = self.client.post(
            reverse('toggle_memo_favorite', kwargs={'memo_id': memo.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        memo.refresh_from_db()
        self.assertTrue(memo.is_favorite)
