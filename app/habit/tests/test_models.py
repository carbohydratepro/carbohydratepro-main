"""習慣トラッカーのモデル・ビューテスト"""
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from app.habit.models import Habit, HabitRecord
from app.habit import selectors

User = get_user_model()


class HabitModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass'
        )
        self.habit = Habit.objects.create(
            user=self.user, title='読書', frequency='daily',
            coefficient=1, is_positive=True,
        )

    def test_str(self) -> None:
        self.assertEqual(str(self.habit), '読書')

    def test_signed_coefficient_positive(self) -> None:
        self.assertEqual(self.habit.signed_coefficient, 1)

    def test_signed_coefficient_negative(self) -> None:
        self.habit.is_positive = False
        self.assertEqual(self.habit.signed_coefficient, -1)

    def test_color_positive(self) -> None:
        self.assertEqual(self.habit.color, '#28a745')

    def test_color_negative(self) -> None:
        self.habit.is_positive = False
        self.assertEqual(self.habit.color, '#dc3545')

    def test_habit_record_unique_together(self) -> None:
        today = date.today()
        HabitRecord.objects.create(habit=self.habit, date=today)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            HabitRecord.objects.create(habit=self.habit, date=today)

    def test_habit_record_effective_signed_coefficient_default(self) -> None:
        today = date.today()
        record = HabitRecord.objects.create(habit=self.habit, date=today)
        self.assertEqual(record.effective_signed_coefficient, 1)

    def test_habit_record_effective_signed_coefficient_override(self) -> None:
        today = date.today()
        record = HabitRecord.objects.create(habit=self.habit, date=today, coefficient=5)
        self.assertEqual(record.effective_signed_coefficient, 5)

    def test_habit_record_effective_signed_coefficient_negative_override(self) -> None:
        self.habit.is_positive = False
        self.habit.save()
        today = date.today()
        record = HabitRecord.objects.create(habit=self.habit, date=today, coefficient=3)
        self.assertEqual(record.effective_signed_coefficient, -3)


class HabitSelectorsTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testuser2', email='test2@example.com', password='pass'
        )
        self.habit_good = Habit.objects.create(
            user=self.user, title='運動', frequency='daily',
            coefficient=2, is_positive=True,
        )
        self.habit_bad = Habit.objects.create(
            user=self.user, title='飲酒', frequency='daily',
            coefficient=1, is_positive=False,
        )

    def test_get_habits_returns_active(self) -> None:
        habits = selectors.get_habits(self.user)
        self.assertEqual(habits.count(), 2)

    def test_get_habits_excludes_inactive(self) -> None:
        self.habit_bad.is_active = False
        self.habit_bad.save()
        habits = selectors.get_habits(self.user)
        self.assertEqual(habits.count(), 1)

    def test_get_habits_frequency_order(self) -> None:
        """日 → 週 → 月 の順になること"""
        Habit.objects.create(user=self.user, title='月次', frequency='monthly', coefficient=1, is_positive=True)
        Habit.objects.create(user=self.user, title='週次', frequency='weekly', coefficient=1, is_positive=True)
        habits = list(selectors.get_habits(self.user))
        freqs = [h.frequency for h in habits]
        # daily が先頭にまとまること
        self.assertEqual(freqs[0], 'daily')
        self.assertEqual(freqs[1], 'daily')
        self.assertIn('weekly', freqs)
        self.assertEqual(freqs[-1], 'monthly')

    def test_get_heatmap_data_accumulates_scores(self) -> None:
        today = date.today()
        HabitRecord.objects.create(habit=self.habit_good, date=today)
        HabitRecord.objects.create(habit=self.habit_bad, date=today)
        data = selectors.get_heatmap_data(self.user, end_date=today)
        # +2 + (-1) = 1
        self.assertAlmostEqual(data[today.isoformat()], 1.0)

    def test_get_heatmap_data_score_zero_key_exists(self) -> None:
        """相殺されてスコア0でもキーが存在すること"""
        habit_neg = Habit.objects.create(
            user=self.user, title='相殺', frequency='daily',
            coefficient=2, is_positive=False,
        )
        today = date.today()
        HabitRecord.objects.create(habit=self.habit_good, date=today)
        HabitRecord.objects.create(habit=habit_neg, date=today)
        data = selectors.get_heatmap_data(self.user, end_date=today)
        self.assertIn(today.isoformat(), data)
        self.assertAlmostEqual(data[today.isoformat()], 0.0)

    def test_get_heatmap_data_uses_record_coefficient(self) -> None:
        """記録時に上書きした係数が使われること"""
        today = date.today()
        HabitRecord.objects.create(habit=self.habit_good, date=today, coefficient=5)
        data = selectors.get_heatmap_data(self.user, end_date=today)
        self.assertAlmostEqual(data[today.isoformat()], 5.0)

    def test_get_today_status_completed_flag(self) -> None:
        today = date.today()
        HabitRecord.objects.create(habit=self.habit_good, date=today)
        status = selectors.get_today_status(self.user, today)
        completed = {s['id']: s['completed'] for s in status}
        self.assertTrue(completed[self.habit_good.id])
        self.assertFalse(completed[self.habit_bad.id])

    def test_get_week_data(self) -> None:
        today = date.today()
        dow = today.weekday()
        week_start = today - timedelta(days=dow)
        HabitRecord.objects.create(habit=self.habit_good, date=today)
        rows = selectors.get_week_data(self.user, week_start)
        good_row = next(r for r in rows if r['id'] == self.habit_good.id)
        self.assertEqual(good_row['done_count'], 1)


class HabitViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='viewuser', email='view@example.com', password='pass'
        )
        self.user.is_email_verified = True
        self.user.save()
        self.client = Client()
        self.client.login(email='view@example.com', password='pass')
        self.habit = Habit.objects.create(
            user=self.user, title='ジョギング', frequency='daily',
            coefficient=2, is_positive=True,
        )

    def test_dashboard_accessible(self) -> None:
        resp = self.client.get(reverse('habit_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_with_past_date(self) -> None:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = self.client.get(reverse('habit_dashboard') + f'?date={yesterday}')
        self.assertEqual(resp.status_code, 200)

    def test_create_habit(self) -> None:
        resp = self.client.post(reverse('create_habit'), {
            'title': '瞑想', 'frequency': 'daily',
            'coefficient': 1, 'is_positive': 'true',
            'weekly_goal': 0, 'monthly_goal': 0,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Habit.objects.filter(title='瞑想', user=self.user).exists())

    def test_toggle_habit_creates_record(self) -> None:
        today = date.today().isoformat()
        resp = self.client.post(reverse('toggle_habit'), {
            'habit_id': self.habit.id, 'date': today,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['completed'])
        self.assertTrue(HabitRecord.objects.filter(habit=self.habit, date=today).exists())

    def test_toggle_habit_with_coefficient_override(self) -> None:
        today = date.today().isoformat()
        resp = self.client.post(reverse('toggle_habit'), {
            'habit_id': self.habit.id, 'date': today, 'coefficient': '5',
        })
        self.assertEqual(resp.status_code, 200)
        record = HabitRecord.objects.get(habit=self.habit, date=today)
        self.assertEqual(record.coefficient, 5)

    def test_toggle_habit_deletes_record_on_second_call(self) -> None:
        today = date.today().isoformat()
        self.client.post(reverse('toggle_habit'), {'habit_id': self.habit.id, 'date': today})
        resp = self.client.post(reverse('toggle_habit'), {'habit_id': self.habit.id, 'date': today})
        data = resp.json()
        self.assertFalse(data['completed'])
        self.assertFalse(HabitRecord.objects.filter(habit=self.habit, date=today).exists())

    def test_toggle_habit_rejects_future_date(self) -> None:
        future = (date.today() + timedelta(days=1)).isoformat()
        resp = self.client.post(reverse('toggle_habit'), {'habit_id': self.habit.id, 'date': future})
        self.assertEqual(resp.status_code, 400)

    def test_habit_status_json(self) -> None:
        today = date.today().isoformat()
        resp = self.client.get(reverse('habit_status_json') + f'?date={today}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('status', data)

    def test_habit_heatmap_json(self) -> None:
        resp = self.client.get(reverse('habit_heatmap_json'))
        self.assertEqual(resp.status_code, 200)

    def test_habit_heatmap_json_with_year(self) -> None:
        resp = self.client.get(reverse('habit_heatmap_json') + '?year=2026')
        self.assertEqual(resp.status_code, 200)

    def test_delete_habit(self) -> None:
        resp = self.client.post(reverse('delete_habit', args=[self.habit.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Habit.objects.filter(id=self.habit.id).exists())

    def test_habit_list_accessible(self) -> None:
        resp = self.client.get(reverse('habit_list'))
        self.assertEqual(resp.status_code, 200)

    def test_habit_status_json_old_date(self) -> None:
        """habit_status_json は過去7日より古い日付にも対応すること（週/年ビュー詳細表示のため）"""
        old_date = (date.today() - timedelta(days=30)).isoformat()
        resp = self.client.get(reverse('habit_status_json') + f'?date={old_date}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('status', data)

    def test_habit_status_json_rejects_future_date(self) -> None:
        future = (date.today() + timedelta(days=1)).isoformat()
        resp = self.client.get(reverse('habit_status_json') + f'?date={future}')
        self.assertEqual(resp.status_code, 400)
