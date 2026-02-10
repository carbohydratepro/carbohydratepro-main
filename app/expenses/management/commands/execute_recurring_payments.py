from datetime import date

from django.core.management.base import BaseCommand

from app.expenses.models import RecurringPayment


class Command(BaseCommand):
    help = '定期支払いを実行し、該当する取引を自動作成する'

    def add_arguments(self, parser: 'ArgumentParser') -> None:
        parser.add_argument(
            '--date',
            type=str,
            help='実行日（YYYY-MM-DD形式）。未指定の場合は本日',
        )

    def handle(self, *args: object, **options: object) -> None:
        date_str = options.get('date')
        if date_str:
            target_date = date.fromisoformat(str(date_str))
        else:
            target_date = date.today()

        recurring_payments = RecurringPayment.objects.filter(
            is_active=True,
        ).select_related('category', 'payment_method', 'user')

        executed_count = 0
        for recurring in recurring_payments:
            if recurring.should_execute_on(target_date):
                recurring.execute(target_date)
                executed_count += 1
                self.stdout.write(
                    f'  実行: {recurring.user.username} - {recurring.purpose} (¥{recurring.amount})'
                )

        self.stdout.write(
            self.style.SUCCESS(f'{executed_count}件の定期支払いを実行しました。（対象日: {target_date}）')
        )
