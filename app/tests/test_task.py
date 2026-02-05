"""
タスク管理機能のテスト
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from app.task.models import Task, TaskLabel
from app.task.forms import TaskForm, TaskLabelForm


class TaskLabelModelTest(TestCase):
    """タスクラベルモデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )

    def test_create_task_label(self) -> None:
        """タスクラベルの作成テスト"""
        label = TaskLabel.objects.create(
            user=self.user,
            name='重要',
            color='#FF0000'
        )
        self.assertEqual(str(label), '重要')
        self.assertEqual(label.color, '#FF0000')

    def test_label_default_color(self) -> None:
        """デフォルト色のテスト"""
        label = TaskLabel.objects.create(
            user=self.user,
            name='テスト'
        )
        self.assertEqual(label.color, '#6c757d')

    def test_label_ordering(self) -> None:
        """ラベルの並び順テスト（名前順）"""
        TaskLabel.objects.create(user=self.user, name='Zラベル')
        TaskLabel.objects.create(user=self.user, name='Aラベル')
        labels = TaskLabel.objects.filter(user=self.user)
        self.assertEqual(labels[0].name, 'Aラベル')


class TaskModelTest(TestCase):
    """タスクモデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.label = TaskLabel.objects.create(
            user=self.user,
            name='仕事'
        )

    def test_create_basic_task(self) -> None:
        """基本的なタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='会議の準備',
            priority='high',
            status='not_started',
            description='資料を作成する'
        )
        self.assertEqual(str(task), '会議の準備 - 未着手')
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.status, 'not_started')

    def test_create_task_with_label(self) -> None:
        """ラベル付きタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='プロジェクト進捗報告',
            label=self.label,
            priority='medium',
            status='in_progress'
        )
        self.assertEqual(task.label, self.label)
        self.assertEqual(task.label.name, '仕事')

    def test_create_task_with_dates(self) -> None:
        """日時付きタスクの作成テスト"""
        start = timezone.now()
        end = start + timedelta(hours=2)
        task = Task.objects.create(
            user=self.user,
            title='ミーティング',
            start_date=start,
            end_date=end,
            all_day=False,
            status='not_started'
        )
        self.assertEqual(task.start_date, start)
        self.assertEqual(task.end_date, end)
        self.assertFalse(task.all_day)

    def test_create_all_day_task(self) -> None:
        """終日タスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='休暇',
            all_day=True,
            start_date=timezone.now(),
            status='not_started'
        )
        self.assertTrue(task.all_day)

    def test_create_daily_recurring_task(self) -> None:
        """毎日繰り返しタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='日報作成',
            frequency='daily',
            repeat_interval=1,
            repeat_count=30,
            status='not_started'
        )
        self.assertEqual(task.frequency, 'daily')
        self.assertEqual(task.repeat_interval, 1)
        self.assertEqual(task.repeat_count, 30)

    def test_create_weekly_recurring_task(self) -> None:
        """毎週繰り返しタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='週次ミーティング',
            frequency='weekly',
            repeat_interval=1,
            repeat_count=10,
            status='not_started'
        )
        self.assertEqual(task.frequency, 'weekly')
        self.assertEqual(task.repeat_count, 10)

    def test_create_monthly_recurring_task(self) -> None:
        """毎月繰り返しタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='月次報告',
            frequency='monthly',
            repeat_interval=1,
            repeat_count=12,
            status='not_started'
        )
        self.assertEqual(task.frequency, 'monthly')

    def test_create_yearly_recurring_task(self) -> None:
        """毎年繰り返しタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title='年次レビュー',
            frequency='yearly',
            repeat_interval=1,
            repeat_count=5,
            status='not_started'
        )
        self.assertEqual(task.frequency, 'yearly')

    def test_task_with_parent(self) -> None:
        """親タスクを持つタスクの作成テスト（繰り返しインスタンス）"""
        parent_task = Task.objects.create(
            user=self.user,
            title='定期タスク',
            frequency='weekly',
            status='not_started'
        )
        child_task = Task.objects.create(
            user=self.user,
            title='定期タスク - インスタンス',
            parent_task=parent_task,
            status='completed'
        )
        self.assertEqual(child_task.parent_task, parent_task)
        self.assertIn(child_task, parent_task.recurring_instances.all())

    def test_task_ordering(self) -> None:
        """タスクの並び順テスト（作成日降順）"""
        task1 = Task.objects.create(
            user=self.user,
            title='古いタスク',
            status='not_started'
        )
        task2 = Task.objects.create(
            user=self.user,
            title='新しいタスク',
            status='not_started'
        )
        tasks = Task.objects.filter(user=self.user)
        self.assertEqual(tasks[0], task2)
        self.assertEqual(tasks[1], task1)

    def test_priority_choices(self) -> None:
        """優先度の選択肢テスト"""
        choices = dict(Task.PRIORITY_CHOICES)
        self.assertIn('high', choices)
        self.assertIn('medium', choices)
        self.assertIn('low', choices)

    def test_status_choices(self) -> None:
        """ステータスの選択肢テスト"""
        choices = dict(Task.STATUS_CHOICES)
        self.assertIn('not_started', choices)
        self.assertIn('in_progress', choices)
        self.assertIn('completed', choices)


class TaskFormTest(TestCase):
    """タスクフォームのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.label = TaskLabel.objects.create(user=self.user, name='テスト')

    def test_valid_basic_form(self) -> None:
        """有効な基本フォームのテスト"""
        form = TaskForm(
            user=self.user,
            data={
                'title': 'テストタスク',
                'priority': 'medium',
                'status': 'not_started',
                'description': 'テスト内容',
                'frequency': '',
                'repeat_interval': 1,
                'all_day': False,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_without_title_invalid(self) -> None:
        """タイトルなしのフォームが無効であることをテスト"""
        form = TaskForm(
            user=self.user,
            data={
                'title': '',
                'priority': 'low',
                'status': 'not_started',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_with_label(self) -> None:
        """ラベル付きフォームのテスト"""
        form = TaskForm(
            user=self.user,
            data={
                'title': '新機能開発',
                'label': self.label.id,
                'priority': 'high',
                'status': 'in_progress',
                'frequency': '',
                'repeat_interval': 1,
            }
        )
        self.assertTrue(form.is_valid())

    def test_recurring_form_without_repeat_count_invalid(self) -> None:
        """繰り返しタスクで繰り返し回数なしが無効であることをテスト"""
        form = TaskForm(
            user=self.user,
            data={
                'title': '繰り返しタスク',
                'frequency': 'daily',
                'repeat_interval': 1,
                'repeat_count': '',
                'priority': 'medium',
                'status': 'not_started',
            }
        )
        self.assertFalse(form.is_valid())

    def test_form_start_date_without_time_invalid(self) -> None:
        """終日でない場合に開始日のみで開始時刻なしが無効であることをテスト"""
        form = TaskForm(
            user=self.user,
            data={
                'title': 'テストタスク',
                'priority': 'medium',
                'status': 'not_started',
                'start_date': timezone.now().date(),
                'all_day': False,
                'frequency': '',
                'repeat_interval': 1,
            }
        )
        self.assertFalse(form.is_valid())

    def test_form_all_day_valid(self) -> None:
        """終日タスクのフォームが有効であることをテスト"""
        form = TaskForm(
            user=self.user,
            data={
                'title': '終日イベント',
                'priority': 'medium',
                'status': 'not_started',
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date(),
                'all_day': True,
                'frequency': '',
                'repeat_interval': 1,
            }
        )
        self.assertTrue(form.is_valid())


class TaskLabelFormTest(TestCase):
    """タスクラベルフォームのテスト"""

    def test_valid_form(self) -> None:
        """有効なフォームのテスト"""
        form = TaskLabelForm(data={
            'name': '緊急',
            'color': '#FFA500'
        })
        self.assertTrue(form.is_valid())

    def test_form_without_name_invalid(self) -> None:
        """名前なしのフォームが無効であることをテスト"""
        form = TaskLabelForm(data={
            'name': '',
            'color': '#FFA500'
        })
        self.assertFalse(form.is_valid())


class TaskViewTest(TestCase):
    """タスク管理ビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.label = TaskLabel.objects.create(user=self.user, name='テスト')
        self.client.login(username='test@example.com', password='testpass123')

    def test_task_list_requires_login(self) -> None:
        """タスク一覧に認証が必要であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 302)

    def test_task_list_view(self) -> None:
        """タスク一覧ビューのテスト"""
        Task.objects.create(
            user=self.user,
            title='テストタスク',
            priority='medium',
            status='not_started'
        )
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

    def test_task_list_with_search(self) -> None:
        """検索機能のテスト"""
        Task.objects.create(
            user=self.user,
            title='検索対象タスク',
            priority='medium',
            status='not_started'
        )
        response = self.client.get(reverse('task_list'), {'search': '検索対象'})
        self.assertEqual(response.status_code, 200)

    def test_task_list_filter_by_status(self) -> None:
        """ステータスでのフィルタリングテスト"""
        response = self.client.get(reverse('task_list'), {'status': 'not_started'})
        self.assertEqual(response.status_code, 200)

    def test_task_list_filter_by_priority(self) -> None:
        """優先度でのフィルタリングテスト"""
        response = self.client.get(reverse('task_list'), {'priority': 'high'})
        self.assertEqual(response.status_code, 200)

    def test_task_list_filter_by_label(self) -> None:
        """ラベルでのフィルタリングテスト"""
        response = self.client.get(reverse('task_list'), {'label': self.label.id})
        self.assertEqual(response.status_code, 200)

    def test_create_task_view_get(self) -> None:
        """タスク作成ビュー（GET）のテスト"""
        response = self.client.get(reverse('create_task'))
        self.assertEqual(response.status_code, 200)

    def test_create_task_view_post(self) -> None:
        """タスク作成ビュー（POST）のテスト"""
        data = {
            'title': '新しいタスク',
            'priority': 'high',
            'status': 'not_started',
            'description': '重要な作業',
            'frequency': '',
            'repeat_interval': 1,
            'all_day': False,
        }
        response = self.client.post(reverse('create_task'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='新しいタスク').exists())

    def test_create_recurring_task(self) -> None:
        """繰り返しタスク作成のテスト"""
        data = {
            'title': '毎週のタスク',
            'frequency': 'weekly',
            'repeat_interval': 1,
            'repeat_count': 5,
            'priority': 'medium',
            'status': 'not_started',
            'all_day': False,
        }
        response = self.client.post(reverse('create_task'), data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='毎週のタスク')
        self.assertEqual(task.frequency, 'weekly')
        self.assertEqual(task.repeat_count, 5)

    def test_edit_task_view_get(self) -> None:
        """タスク編集ビュー（GET）のテスト"""
        task = Task.objects.create(
            user=self.user,
            title='編集テスト',
            priority='low',
            status='not_started'
        )
        response = self.client.get(reverse('edit_task', kwargs={'task_id': task.id}))
        self.assertEqual(response.status_code, 200)

    def test_edit_task_view_post(self) -> None:
        """タスク編集ビュー（POST）のテスト"""
        task = Task.objects.create(
            user=self.user,
            title='ステータス変更テスト',
            priority='medium',
            status='not_started'
        )
        data = {
            'title': 'ステータス変更テスト',
            'priority': 'medium',
            'status': 'completed',
            'frequency': '',
            'repeat_interval': 1,
        }
        response = self.client.post(reverse('edit_task', kwargs={'task_id': task.id}), data)
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')

    def test_edit_task_other_user_forbidden(self) -> None:
        """他ユーザーのタスク編集が禁止されることをテスト"""
        User = get_user_model()
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            is_email_verified=True,
        )
        other_task = Task.objects.create(
            user=other_user,
            title='他ユーザータスク',
            priority='medium',
            status='not_started'
        )
        response = self.client.get(reverse('edit_task', kwargs={'task_id': other_task.id}))
        self.assertEqual(response.status_code, 404)

    def test_delete_task_view(self) -> None:
        """タスク削除ビューのテスト"""
        task = Task.objects.create(
            user=self.user,
            title='削除テスト',
            priority='low',
            status='not_started'
        )
        response = self.client.post(reverse('delete_task', kwargs={'task_id': task.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_get_day_tasks_view(self) -> None:
        """日別タスク取得ビューのテスト"""
        today = timezone.now().date()
        Task.objects.create(
            user=self.user,
            title='今日のタスク',
            start_date=timezone.now(),
            priority='medium',
            status='not_started'
        )
        response = self.client.get(reverse('get_day_tasks', kwargs={'date': today.strftime('%Y-%m-%d')}))
        self.assertEqual(response.status_code, 200)

    def test_task_settings_view(self) -> None:
        """タスク設定ビューのテスト"""
        response = self.client.get(reverse('task_settings'))
        self.assertEqual(response.status_code, 200)

    def test_task_settings_add_label(self) -> None:
        """ラベル追加のテスト"""
        initial_count = TaskLabel.objects.filter(user=self.user).count()
        response = self.client.post(reverse('task_settings'), {
            'label': '',
            'label-name': '新ラベル',
            'label-color': '#FF0000'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TaskLabel.objects.filter(user=self.user).count(), initial_count + 1)

    def test_task_settings_edit_label(self) -> None:
        """ラベル編集のテスト"""
        response = self.client.post(reverse('task_settings'), {
            'label_id': self.label.id,
            'edit_label': '',
            'label-name': '更新済みラベル',
            'label-color': '#00FF00'
        })
        self.assertEqual(response.status_code, 302)
        self.label.refresh_from_db()
        self.assertEqual(self.label.name, '更新済みラベル')

    def test_task_settings_delete_label(self) -> None:
        """ラベル削除のテスト"""
        label_to_delete = TaskLabel.objects.create(user=self.user, name='削除用')
        response = self.client.post(reverse('task_settings'), {
            'label_id': label_to_delete.id,
            'delete_label': ''
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TaskLabel.objects.filter(id=label_to_delete.id).exists())


class TaskAjaxViewTest(TestCase):
    """タスクAJAXビューのテスト"""

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

    def test_create_task_ajax_success(self) -> None:
        """AJAX経由でのタスク作成テスト（成功）"""
        data = {
            'title': 'AJAXタスク',
            'priority': 'high',
            'status': 'not_started',
            'frequency': '',
            'repeat_interval': 1,
            'all_day': False,
        }
        response = self.client.post(
            reverse('create_task'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))

    def test_edit_task_ajax_success(self) -> None:
        """AJAX経由でのタスク編集テスト（成功）"""
        task = Task.objects.create(
            user=self.user,
            title='編集対象',
            priority='medium',
            status='not_started'
        )
        data = {
            'title': '編集後タスク',
            'priority': 'high',
            'status': 'in_progress',
            'frequency': '',
            'repeat_interval': 1,
        }
        response = self.client.post(
            reverse('edit_task', kwargs={'task_id': task.id}),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))
