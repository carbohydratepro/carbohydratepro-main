from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_habit_v2'),
    ]

    operations = [
        migrations.AddField(
            model_name='habitrecord',
            name='coefficient',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='使用係数'),
        ),
        migrations.AddField(
            model_name='habitrecord',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='登録日時'),
            preserve_default=False,
        ),
    ]
