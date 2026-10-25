"""隔離したDockerネットワークでTLS・接続元制限・ヘッダー偽装を検証する。"""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'nginx:1.30.6@sha256:a7675fcee220f59b4a99f7098c06a0d5d999c2c0ee37c0211efb780536e5cb20'
spec = importlib.util.spec_from_file_location('origin_security', ROOT / 'scripts/prepare-origin-security.py')
origin_security = importlib.util.module_from_spec(spec)
spec.loader.exec_module(origin_security)


class OriginConfigurationTests(unittest.TestCase):
    def test_rejects_empty_and_worldwide_ranges(self):
        for prefixes in [[], [{'service': 'CLOUDFRONT_ORIGIN_FACING', 'ip_prefix': '0.0.0.0/0'}]]:
            with self.assertRaises(ValueError):
                origin_security.cloudfront_networks({'prefixes': prefixes, 'ipv6_prefixes': []})

    def test_ignores_non_origin_cloudfront_ranges(self):
        data = {'prefixes': [
            {'service': 'CLOUDFRONT', 'ip_prefix': '0.0.0.0/0'},
            {'service': 'CLOUDFRONT_ORIGIN_FACING', 'ip_prefix': '192.0.2.2/32'},
        ], 'ipv6_prefixes': []}
        self.assertEqual(origin_security.cloudfront_networks(data), ['192.0.2.2/32'])


class OriginRuntimeTests(unittest.TestCase):
    def test_tls_and_access_control(self):
        name = 'carbohydratepro-origin-test-' + str(os.getpid())
        temporary_root = ROOT / 'workspace/security-hardening-20261022'
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='origin-test-', dir=temporary_root) as folder:
            work = Path(folder).resolve()
            security = work / 'security'
            certificates = work / 'certificates'
            live = certificates / 'live/lightsail.carbohydratepro.com'
            live.mkdir(parents=True)
            socket_dir = work / 'socket'
            socket_dir.mkdir()
            socket_dir.chmod(0o755)
            static = work / 'static'
            static.mkdir()
            static.chmod(0o755)
            (static / 'app.012345abcdef.css').write_text('body { color: black; }')
            (static / 'app.012345abcdef.css').chmod(0o644)
            (work / 'ranges.json').write_text(json.dumps({'prefixes': [
                {'service': 'CLOUDFRONT_ORIGIN_FACING', 'ip_prefix': '192.0.2.2/32'},
            ], 'ipv6_prefixes': []}))
            origin_security.prepare(work / 'ranges.json', security)
            token = (security / 'origin-token').read_text()
            origin_security.prepare(work / 'ranges.json', security)
            self.assertEqual((security / 'origin-token').read_text(), token)
            self.assertEqual((security / 'origin-token').stat().st_mode & 0o777, 0o600)
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                '-subj', '/CN=carbohydratepro.com', '-addext', 'subjectAltName=DNS:carbohydratepro.com',
                '-keyout', str(live / 'privkey.pem'), '-out', str(live / 'fullchain.pem'),
            ], check=True, capture_output=True)
            (work / 'backend.py').write_text('''
import http.server, json, os, socketserver
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body=json.dumps(dict(self.headers)).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args): pass
server=socketserver.UnixStreamServer('/var/run/gunicorn/gunicorn.sock',Handler)
os.chmod('/var/run/gunicorn/gunicorn.sock',0o666)
server.serve_forever()
''')
            (work / 'client.py').write_text('''
import json, os, ssl, urllib.error, urllib.request
context=ssl.create_default_context(cafile='/test/certificates/live/lightsail.carbohydratepro.com/fullchain.pem')
token=open('/test/security/origin-token').read().strip()
def request(headers, path='/'):
    req=urllib.request.Request('https://carbohydratepro.com'+path,headers=headers)
    try:
        with urllib.request.urlopen(req,context=context,timeout=5) as r:
            return r.status,dict(r.headers),r.read()
    except urllib.error.HTTPError as e:
        return e.code,dict(e.headers),e.read()
good={'X-Carbohydratepro-Origin':token,'X-Forwarded-For':'198.51.100.66, 203.0.113.9','X-Forwarded-Proto':'http'}
if os.environ['TRUSTED']=='1':
    for headers in [{},{'X-Carbohydratepro-Origin':'wrong'}]:
        assert request(headers)[0]==403,'Missing/wrong token was accepted'
    status,headers,body=request(good)
    assert status==200,'Authorized request failed'
    forwarded={k.lower():v for k,v in json.loads(body).items()}
    assert forwarded['x-forwarded-for']=='203.0.113.9','Spoofed IP forwarded'
    assert forwarded['x-real-ip']=='203.0.113.9'
    assert forwarded['x-forwarded-proto']=='https','Spoofed protocol forwarded'
    assert 'x-carbohydratepro-origin' not in forwarded,'Secret leaked to application'
    status,headers,body=request(good,'/static/app.012345abcdef.css')
    assert status==200 and 'immutable' in headers['Cache-Control']
    print('PASS: TLS trust, missing/wrong secret, client IP, spoofed protocol, secret removal, static cache')
else:
    assert request(good)[0]==403,'Untrusted source with valid token was accepted'
    print('PASS: untrusted source blocked even with valid secret')
''')
            containers = []

            def docker(*args, capture=True):
                return subprocess.run(['docker', *args], check=True, capture_output=capture, text=True)

            docker('network', 'create', '--internal', '--subnet', '192.0.2.0/29', name)
            try:
                backend = name + '-backend'
                docker('run', '-d', '--name', backend, '--network', 'none',
                       '-v', str(work) + ':/test:ro', '-v', str(socket_dir) + ':/var/run/gunicorn',
                       '--entrypoint', 'python', 'gunicorn:20.1.0', '/test/backend.py')
                containers.append(backend)
                nginx = name + '-nginx'
                docker('run', '-d', '--name', nginx, '--network', name, '--ip', '192.0.2.4',
                       '-v', str(ROOT / 'nginx/production.conf') + ':/etc/nginx/conf.d/default.conf:ro',
                       '-v', str(security) + ':/etc/nginx/security:ro',
                       '-v', str(certificates) + ':/etc/nginx/certificates:ro',
                       '-v', str(socket_dir) + ':/var/run/gunicorn:ro',
                       '-v', str(static) + ':/var/www/static:ro', IMAGE)
                containers.append(nginx)
                docker('exec', nginx, 'nginx', '-t')
                for trusted, ip in [('1', '192.0.2.2'), ('0', '192.0.2.3')]:
                    result = docker('run', '--rm', '--network', name, '--ip', ip,
                                    '--add-host', 'carbohydratepro.com:192.0.2.4',
                                    '-e', 'TRUSTED=' + trusted, '-v', str(work) + ':/test:ro',
                                    '--entrypoint', 'python', 'gunicorn:20.1.0', '/test/client.py')
                    print(result.stdout.strip())
                logs = docker('logs', nginx)
                self.assertNotIn(token.strip(), logs.stdout + logs.stderr)
                self.assertIn('203.0.113.9 peer=192.0.2.2', logs.stdout)
            except subprocess.CalledProcessError as error:
                detail = (error.stdout or '') + (error.stderr or '')
                for container in containers:
                    result = subprocess.run(['docker', 'logs', container], capture_output=True, text=True)
                    detail += result.stdout + result.stderr
                self.fail(detail.replace(token.strip(), '[REDACTED]'))
            finally:
                for container in reversed(containers):
                    subprocess.run(['docker', 'rm', '-f', container], check=False, capture_output=True)
                subprocess.run(['docker', 'network', 'rm', name], check=False, capture_output=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
