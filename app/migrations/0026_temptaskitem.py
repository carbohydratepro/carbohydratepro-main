from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0025_alter_shoppingitem_options_shoppingitem_is_checked'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TempTaskItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='タイトル')),
                ('status', models.CharField(
                    choices=[('todo', 'やること'), ('doing', 'やってる'), ('done', 'できた')],
                    default='todo',
                    max_length=10,
                    verbose_name='ステータス',
                )),
                ('order', models.IntegerField(default=0, verbose_name='表示順')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='temp_task_items',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': '一時タスク',
                'verbose_name_plural': '一時タスク',
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
