"""既定のスキャンが見逃す固定値と、実際のDocker COPYへの秘密混入を検証する。"""

import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SecretRulesTests(unittest.TestCase):
    def test_new_literal_credentials_are_rejected(self):
        scanner = os.environ.get('GITLEAKS', 'gitleaks')
        for text in [
            "SECRET_KEY = 'django-insecure-" + 'synthetic-test-key-123456789' + "'\n",
            'POSTGRES_PASSWORD=' + 'synthetic-test-password' + '\n',
        ]:
            result = subprocess.run(
                [scanner, 'stdin', '--config', str(ROOT / '.gitleaks.toml'),
                 '--redact=100', '--ignore-gitleaks-allow', '--no-banner'],
                input=text, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)

    def test_ci_exception_only_allows_the_disposable_fixture(self):
        scanner = os.environ.get('GITLEAKS', 'gitleaks')
        with tempfile.TemporaryDirectory(prefix='secret-ci-') as folder:
            workflow = Path(folder) / '.github/workflows/tests.yml'
            workflow.parent.mkdir(parents=True)
            for value, expected in [('ci-only-disposable-postgres', 0),
                                    ('synthetic-unexpected-password', 1)]:
                workflow.write_text('POSTGRES_PASSWORD: ' + value + '\n')
                result = subprocess.run(
                    [scanner, 'dir', folder, '--config', str(ROOT / '.gitleaks.toml'),
                     '--redact=100', '--ignore-gitleaks-allow', '--no-banner'],
                    text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_docker_copy_excludes_private_files(self):
        name = 'carbohydratepro-context-test-' + str(os.getpid())
        private = ['secret.env', '.env.production', 'db.env', 'nested/secret.env',
                   'nested/private.pem', 'nested/id_ed25519', 'backup.dump',
                   'workspace/audit.txt', '.git/config', 'media/upload.png', 'django_debug.log']
        container = None
        with tempfile.TemporaryDirectory(prefix='secret-context-') as folder:
            context = Path(folder)
            shutil.copyfile(ROOT / '.dockerignore', context / '.dockerignore')
            (context / 'Dockerfile').write_text('FROM scratch\nCOPY . /context/\nCMD ["true"]\n')
            (context / 'application.py').write_text('# Application source must remain\n')
            for relative in private:
                path = context / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic private fixture\n')
            try:
                subprocess.run(['docker', 'build', '-q', '-t', name, str(context)],
                               check=True, capture_output=True)
                container = subprocess.check_output(['docker', 'create', name], text=True).strip()
                data = subprocess.check_output(['docker', 'export', container])
                with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                    names = set(archive.getnames())
                self.assertIn('context/application.py', names)
                for relative in private:
                    self.assertNotIn('context/' + relative, names)
            finally:
                if container:
                    subprocess.run(['docker', 'rm', container], check=False, capture_output=True)
                subprocess.run(['docker', 'image', 'rm', name], check=False, capture_output=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
