from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from app.task.models import Task, TaskLabel
from app.task.forms import TaskForm, TaskLabelForm


class TaskModelsTestCase(TestCase):
    """タスク管理機能のモデルテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )

    def test_task_label_creation(self):
        """TaskLabel モデルの作成テスト"""
        label = TaskLabel.objects.create(
            user=self.user,
            name="重要",
            color="#FF0000"
        )
        self.assertEqual(str(label), "重要")
        self.assertEqual(label.color, "#FF0000")

    def test_task_creation_basic(self):
        """Task モデルの基本的な作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title="会議の準備",
            priority="high",
            status="not_started",
            description="資料を作成する"
        )
        
        self.assertEqual(str(task), "会議の準備 - 未着手")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.status, "not_started")

    def test_task_with_label(self):
        """TaskLabel 付きタスクの作成テスト"""
        label = TaskLabel.objects.create(user=self.user, name="仕事")
        task = Task.objects.create(
            user=self.user,
            title="プロジェクト進捗報告",
            label=label,
            priority="medium",
            status="in_progress"
        )
        
        self.assertEqual(task.label, label)
        self.assertEqual(task.label.name, "仕事")

    def test_task_with_dates(self):
        """日付設定ありのタスク作成テスト"""
        start = timezone.now()
        end = start + timedelta(hours=2)
        
        task = Task.objects.create(
            user=self.user,
            title="ミーティング",
            start_date=start,
            end_date=end,
            all_day=False,
            status="not_started"
        )
        
        self.assertEqual(task.start_date, start)
        self.assertEqual(task.end_date, end)
        self.assertFalse(task.all_day)

    def test_task_all_day(self):
        """終日タスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title="休暇",
            all_day=True,
            start_date=timezone.now(),
            status="not_started"
        )
        
        self.assertTrue(task.all_day)

    def test_task_recurring_daily(self):
        """毎日繰り返しタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title="日報作成",
            frequency="daily",
            repeat_interval=1,
            status="not_started"
        )
        
        self.assertEqual(task.frequency, "daily")
        self.assertEqual(task.repeat_interval, 1)

    def test_task_recurring_weekly(self):
        """毎週繰り返しタスクの作成テスト"""
        task = Task.objects.create(
            user=self.user,
            title="週次ミーティング",
            frequency="weekly",
            repeat_interval=1,
            repeat_count=10,
            status="not_started"
        )
        
        self.assertEqual(task.frequency, "weekly")
        self.assertEqual(task.repeat_count, 10)

    def test_task_with_parent(self):
        """親タスクを持つタスクの作成テスト（繰り返しインスタンス）"""
        parent_task = Task.objects.create(
            user=self.user,
            title="定期タスク",
            frequency="weekly",
            status="not_started"
        )
        
        child_task = Task.objects.create(
            user=self.user,
            title="定期タスク - インスタンス",
            parent_task=parent_task,
            status="completed"
        )
        
        self.assertEqual(child_task.parent_task, parent_task)
        self.assertIn(child_task, parent_task.recurring_instances.all())

    def test_task_ordering(self):
        """Task の並び順テスト（作成日降順）"""
        task1 = Task.objects.create(
            user=self.user,
            title="古いタスク",
            status="not_started"
        )
        
        task2 = Task.objects.create(
            user=self.user,
            title="新しいタスク",
            status="not_started"
        )
        
        tasks = Task.objects.all()
        self.assertEqual(tasks[0], task2)  # 新しいタスクが最初
        self.assertEqual(tasks[1], task1)


class TaskFormsTestCase(TestCase):
    """タスク管理機能のフォームテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )

    def test_task_form_valid(self):
        """TaskForm の正常なバリデーションテスト"""
        form = TaskForm(
            user=self.user,
            data={
                "title": "テストタスク",
                "priority": "medium",
                "status": "not_started",
                "description": "テスト内容",
                "frequency": "",
                "repeat_interval": 1,
                "all_day": False,
            }
        )
        self.assertTrue(form.is_valid())

    def test_task_form_without_title(self):
        """TaskForm のタイトルなしのテスト"""
        form = TaskForm(
            user=self.user,
            data={
                "title": "",
                "priority": "low",
                "status": "not_started",
            }
        )
        self.assertFalse(form.is_valid())

    def test_task_form_with_label(self):
        """TaskForm のラベル付きテスト"""
        label = TaskLabel.objects.create(user=self.user, name="プロジェクト")
        form = TaskForm(
            user=self.user,
            data={
                "title": "新機能開発",
                "label": label.id,
                "priority": "high",
                "status": "in_progress",
                "frequency": "",
                "repeat_interval": 1,
            }
        )
        self.assertTrue(form.is_valid())

    def test_task_label_form_valid(self):
        """TaskLabelForm の正常なバリデーションテスト"""
        form = TaskLabelForm(data={
            "name": "緊急",
            "color": "#FFA500"
        })
        self.assertTrue(form.is_valid())


class TaskViewsTestCase(TestCase):
    """タスク管理機能のビューテスト"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_email_verified=True,
        )
        self.client.login(username=self.user.email, password="testpass123")

    def test_task_list_view(self):
        """タスク一覧ビューのテスト"""
        Task.objects.create(
            user=self.user,
            title="テストタスク",
            priority="medium",
            status="not_started"
        )
        
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "テストタスク")

    def test_task_list_view_requires_login(self):
        """ログインしていない場合のアクセステスト"""
        self.client.logout()
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, 302)

    def test_create_task_view(self):
        """タスク作成ビューのテスト"""
        response = self.client.get(reverse("create_task"))
        self.assertEqual(response.status_code, 200)

    def test_create_task_post(self):
        """タスク作成POSTリクエストのテスト"""
        data = {
            "title": "新しいタスク",
            "priority": "high",
            "status": "not_started",
            "description": "重要な作業",
            "frequency": "",
            "repeat_interval": 1,
            "all_day": False,
        }
        response = self.client.post(reverse("create_task"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title="新しいタスク").exists())

    def test_update_task_view(self):
        """タスク更新ビューのテスト"""
        task = Task.objects.create(
            user=self.user,
            title="更新テスト",
            priority="low",
            status="not_started"
        )
        
        response = self.client.get(reverse("update_task", args=[task.id]))
        self.assertEqual(response.status_code, 200)

    def test_update_task_status(self):
        """タスクステータス更新のテスト"""
        task = Task.objects.create(
            user=self.user,
            title="ステータス変更テスト",
            priority="medium",
            status="not_started"
        )
        
        data = {
            "title": "ステータス変更テスト",
            "priority": "medium",
            "status": "completed",
            "frequency": "",
            "repeat_interval": 1,
        }
        response = self.client.post(reverse("update_task", args=[task.id]), data)
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_delete_task(self):
        """タスク削除のテスト"""
        task = Task.objects.create(
            user=self.user,
            title="削除テスト",
            priority="low",
            status="not_started"
        )
        
        response = self.client.post(reverse("delete_task", args=[task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_task_label_list_view(self):
        """タスクラベル一覧ビューのテスト"""
        TaskLabel.objects.create(user=self.user, name="テストラベル")
        
        response = self.client.get(reverse("task_label_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "テストラベル")

    def test_create_recurring_task(self):
        """繰り返しタスク作成のテスト"""
        data = {
            "title": "毎週のタスク",
            "frequency": "weekly",
            "repeat_interval": 1,
            "repeat_count": 5,
            "priority": "medium",
            "status": "not_started",
            "all_day": False,
        }
        response = self.client.post(reverse("create_task"), data)
        self.assertEqual(response.status_code, 302)
        
        task = Task.objects.get(title="毎週のタスク")
        self.assertEqual(task.frequency, "weekly")
        self.assertEqual(task.repeat_count, 5)
