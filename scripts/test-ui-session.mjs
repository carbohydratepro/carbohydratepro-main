// ローカル専用。既存アカウントをリセットせず、一意なE2Eアカウントを作って後始末する。
import { randomBytes } from 'node:crypto';
import { spawnSync } from 'node:child_process';

const suffix = randomBytes(8).toString('hex');
const credentials = {
  email: `ui-e2e-${suffix}@example.invalid`,
  username: `ui-e2e-${suffix}`,
  password: randomBytes(24).toString('base64url'),
};
const bootstrap = `
import django, json, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings.development'
django.setup()
from django.contrib.auth import get_user_model
from django.db import transaction
from app.expenses.models import Category, PaymentMethod
from app.habit.models import Habit
from app.memo.models import Memo, MemoType
data = json.load(sys.stdin)
User = get_user_model()
with transaction.atomic():
    user = User.objects.create_user(**data, is_email_verified=True, is_active=True)
    Category.objects.create(user=user, name='E2E食費', chart_color='#33518e')
    PaymentMethod.objects.create(user=user, name='E2E現金')
    MemoType.objects.create(user=user, name='E2Eメモ')
    Habit.objects.create(user=user, title='E2E毎日の習慣')
print(json.dumps({'pk': user.pk}))
`;
const cleanup = `
import django, json, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings.development'
django.setup()
from django.contrib.auth import get_user_model
from django.db import transaction
from app.memo.models import Memo
data = json.load(sys.stdin)
assert data['email'].startswith('ui-e2e-') and data['email'].endswith('@example.invalid')
with transaction.atomic():
    user = get_user_model().objects.get(pk=data['pk'], email=data['email'], username=data['username'])
    Memo.objects.filter(user=user).delete()
    user.delete()
print('一時UIテストユーザーと関連データを削除しました。')
`;
function django(code, input) {
  const result = spawnSync('docker-compose', ['-f', 'docker-compose-dev.yml', 'exec', '-T', 'gunicorn', 'python', '-c', code], {
    input: JSON.stringify(input), encoding: 'utf8', cwd: new URL('../', import.meta.url),
  });
  if (result.status !== 0) throw new Error(result.stderr || '開発コンテナでのテスト準備に失敗しました。');
  return result.stdout.trim();
}

const identity = JSON.parse(django(bootstrap, credentials));
try {
  const files = process.argv.slice(2);
  if (!files.length) throw new Error('対象のPlaywrightテストファイルを指定してください。');
  const result = spawnSync('npm', ['run', 'test:e2e', '--', ...files], {
    stdio: 'inherit', cwd: new URL('../', import.meta.url),
    env: { ...process.env, E2E_BASE_URL: 'http://localhost:8000', E2E_USER_EMAIL: credentials.email, E2E_USER_PASSWORD: credentials.password },
  });
  process.exitCode = result.status ?? 1;
} finally {
  console.log(django(cleanup, { ...identity, email: credentials.email, username: credentials.username }));
}
