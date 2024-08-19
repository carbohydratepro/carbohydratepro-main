from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from app.models import PaymentMethod, Category

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_payment_method_and_category(sender, instance, created, **kwargs):
    if created:
        PaymentMethod.objects.create(user=instance, name="現金")
        Category.objects.create(user=instance, name="食費")
