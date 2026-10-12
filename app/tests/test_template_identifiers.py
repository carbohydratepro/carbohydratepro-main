"""桁区切り設定が機械処理用IDに混入しないことを検証する。"""

import re
from decimal import Decimal

from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.habit.models import Habit
from tests.factories import (
    CategoryFactory, MemoFactory, MemoTypeFactory, PaymentMethodFactory,
    ShoppingItemFactory, TaskLabelFactory, TransactionFactory, UserFactory,
)


@override_settings(USE_THOUSAND_SEPARATOR=True, LANGUAGE_CODE='ja')
class TemplateIdentifierTest(SimpleTestCase):
    def test_all_numeric_identifier_expressions_are_unlocalized(self) -> None:
        """ID出力を全テンプレートから抽出し、1000以上でも桁区切りされない。"""
        expression = re.compile(r'{{\s*([\w.]+\.(?:id|pk))\s*(?:\|[^}]*)?}}')
        count = 0
        for root in ('app/templates', 'auth_app/templates'):
            for path in (settings.BASE_DIR / root).rglob('*.html'):
                source = path.read_text()
                matches = list(expression.finditer(source))
                if not matches:
                    continue
                get_template(str(path.relative_to(settings.BASE_DIR / root)))
                loads = '\n'.join(re.findall(r'{%\s*load\s+.*?%}', source))
                for match in matches:
                    name = match.group(1)
                    # ModelFormのhidden BoundFieldはID数値そのものではない。
                    if name in ('step_form.id', 'step_formset.empty_form.id'):
                        continue
                    for value in (999, 1000, 1234, 1000001):
                        context = value
                        for part in reversed(name.split('.')):
                            context = {part: context}
                        with self.subTest(template=str(path), expression=name, value=value):
                            rendered = Template(loads + match.group()).render(Context(context))
                            self.assertEqual(rendered.strip(), str(value))
                    count += 1
        self.assertGreater(count, 100)


@override_settings(USE_THOUSAND_SEPARATOR=True, LANGUAGE_CODE='ja')
class ExpenseIdentifierTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.category = CategoryFactory(id=1234, user=self.user)
        self.payment = PaymentMethodFactory(id=1234, user=self.user)

    def test_large_ids_survive_list_partial_edit_and_save(self) -> None:
        for record_id in (999, 1000, 1234, 1000001):
            with self.subTest(record_id=record_id):
                transaction = TransactionFactory(
                    id=record_id, user=self.user, category=self.category,
                    payment_method=self.payment, amount=Decimal('1234'),
                    date=timezone.now(),
                )
                params = {'target_date': timezone.localdate().strftime('%Y-%m')}
                for headers in ({}, {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}):
                    response = self.client.get(reverse('expense_list'), params, **headers)
                    self.assertContains(response, f'openEditModal({record_id})')
                    self.assertContains(response, f'data-item-id="{record_id}"')
                    self.assertContains(response, f'data-bulk-id="{record_id}"')
                    self.assertContains(response, '¥1,234')
                url = reverse('edit_expenses', args=[transaction.pk])
                response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertContains(response, 'id="editTransactionForm"')
                self.assertContains(response, 'value="1234" selected')
                response = self.client.post(url, {
                    'date': timezone.localdate().isoformat(), 'amount': '2345',
                    'purpose': '編集後', 'transaction_type': 'expense',
                    'major_category': 'variable', 'category': self.category.pk,
                    'payment_method': self.payment.pk,
                }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertJSONEqual(response.content, {'success': True})
                transaction.refresh_from_db()
                self.assertEqual(transaction.amount, Decimal('2345'))
                self.assertEqual(transaction.purpose, '編集後')

    def test_filter_ids_are_not_localized(self) -> None:
        response = self.client.get(reverse('expense_list'))
        self.assertContains(response, 'name="category" value="1234"')
        self.assertContains(response, 'name="payment_method" value="1234"')

    def test_edit_is_still_scoped_to_owner(self) -> None:
        transaction = TransactionFactory(id=1234)
        url = reverse('edit_expenses', args=[transaction.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'purpose': '変更不可'}).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_other_lists_use_plain_ids(self) -> None:
        MemoFactory(id=1234, user=self.user)
        ShoppingItemFactory(id=1234, user=self.user)
        Habit.objects.create(id=1234, user=self.user, title='大きなIDの習慣')
        for url_name, marker in (
            ('memo_list', 'data-item-id="1234"'),
            ('shopping_list', 'data-item-id="1234"'),
            ('habit_list', 'data-habit-id="1234"'),
        ):
            with self.subTest(screen=url_name):
                response = self.client.get(reverse(url_name))
                self.assertContains(response, marker)

    def test_settings_modal_targets_and_hidden_ids_match(self) -> None:
        MemoTypeFactory(id=1234, user=self.user)
        TaskLabelFactory(id=1234, user=self.user)
        for url_name, target, field in (
            ('expenses_settings', 'editPaymentModal1234', 'payment_id'),
            ('expenses_settings', 'editPurposeModal1234', 'purpose_id'),
            ('memo_settings', 'editMemoTypeModal1234', 'memo_type_id'),
            ('task_settings', 'editLabelModal1234', 'label_id'),
        ):
            with self.subTest(screen=url_name, field=field):
                response = self.client.get(reverse(url_name))
                self.assertContains(response, f'id="{target}"')
                self.assertContains(response, f'data-target="#{target}"')
                self.assertContains(response, f'name="{field}" value="1234"')
