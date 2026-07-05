from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q

from app.expenses.models import Category, PaymentMethod
from app.memo.services import ensure_default_memo_types


class Command(BaseCommand):
    help = "Create or reset the Playwright E2E test user."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--email", required=True)
        parser.add_argument("--username", default="e2e-user")
        parser.add_argument("--password", required=True)
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        email = str(options["email"])
        username = str(options["username"])
        password = str(options["password"])
        reset = bool(options["reset"])
        User = get_user_model()

        if reset:
            User.objects.filter(Q(email=email) | Q(username=username)).delete()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "is_email_verified": True,
                "is_active": True,
            },
        )

        user.username = username
        user.is_email_verified = True
        user.is_active = True
        user.set_password(password)
        user.save()

        PaymentMethod.objects.get_or_create(user=user, name="現金")
        Category.objects.get_or_create(user=user, name="食費", defaults={"chart_color": "#4ECDC4"})
        ensure_default_memo_types()

        action = "created" if created or reset else "updated"
        self.stdout.write(self.style.SUCCESS(f"E2E user {action}: {email}"))
