"""HTTPS移行後のNginxとLightsailをAWS公式のCloudFront範囲へ同期する。"""

import argparse
import importlib.util
import ipaddress
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('prepare_origin', SCRIPT_DIR / 'prepare-origin-security.py')
prepare_origin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_origin)
IMAGE = 'nginx:1.30.6@sha256:a7675fcee220f59b4a99f7098c06a0d5d999c2c0ee37c0211efb780536e5cb20'


def normalize(ports: list[dict]) -> list[dict]:
    return sorted([
        {key: sorted(port.get(key, [])) if key in ('cidrs', 'ipv6Cidrs', 'cidrListAliases')
         else port[key]
         for key in ('fromPort', 'toPort', 'protocol', 'cidrs', 'ipv6Cidrs', 'cidrListAliases')}
        for port in ports if port.get('state', 'open') == 'open'
    ], key=lambda port: (port['protocol'], port['fromPort'], port['toPort']))


def firewall_plan(ports: list[dict], networks: list[str]) -> list[dict]:
    current = normalize(ports)
    if [(p['protocol'], p['fromPort'], p['toPort']) for p in current] != [
        ('tcp', 22, 22), ('tcp', 443, 443)
    ]:
        raise ValueError('Only the final SSH + HTTPS firewall can be updated automatically')
    ssh = current[0]
    if not ssh['cidrs'] and not ssh['ipv6Cidrs'] and not ssh['cidrListAliases']:
        raise ValueError('SSH recovery access is missing')
    if any(ipaddress.ip_network(x).prefixlen == 0 for x in ssh['cidrs'] + ssh['ipv6Cidrs']):
        raise ValueError('SSH must not be open worldwide')
    parsed = [ipaddress.ip_network(x) for x in networks]
    if any(x.prefixlen == 0 for x in parsed):
        raise ValueError('Worldwide origin access is forbidden')
    https = dict(current[1], cidrListAliases=[])
    for version, key in [(4, 'cidrs'), (6, 'ipv6Cidrs')]:
        ranges = list(ipaddress.collapse_addresses(x for x in parsed if x.version == version))
        if not ranges or len(ranges) + len(ssh[key]) + len(ssh['cidrListAliases']) > 60:
            raise ValueError('Missing IP family or Lightsail firewall limit exceeded')
        https[key] = [str(x) for x in ranges]
    return normalize([ssh, https])


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120).stdout


def sync(args: argparse.Namespace) -> None:
    if os.geteuid() != 0:
        raise PermissionError('Run as root using the dedicated maintenance credentials')
    aws = ['aws', '--region', args.region, '--output', 'json', 'lightsail']
    current = json.loads(run(*aws, 'get-instance-port-states', '--instance-name', args.instance))
    with urllib.request.urlopen('https://ip-ranges.amazonaws.com/ip-ranges.json', timeout=30) as r:
        document = json.load(r)
    networks = prepare_origin.cloudfront_networks(document)
    planned = firewall_plan(current['portStates'], networks)
    security = Path('/etc/carbohydratepro/nginx')
    if not args.apply:
        print(f'Validated {len(networks)} ranges; firewall and files unchanged (check mode)')
        return
    # 本番トークンの再発行はしない。未準備なら失敗させる。
    if not (security / 'origin-token').is_file():
        raise ValueError('Existing origin token is required')
    with tempfile.TemporaryDirectory(prefix='origin-ranges-') as folder:
        staging = Path(folder)
        ranges = staging / 'ranges.json'
        ranges.write_text(json.dumps(document))
        generated = staging / 'security'
        generated.mkdir(mode=0o700)
        shutil.copyfile(security / 'origin-token', generated / 'origin-token')
        prepare_origin.prepare(ranges, generated)
        files = ['cloudfront-realip.conf', 'cloudfront-peers.conf']
        changed = any((generated / name).read_bytes() != (security / name).read_bytes()
                      for name in files)
        if changed:
            # 現在の証明書・Nginx設定と新範囲を別コンテナで構文検証してから反映する。
            run('docker', 'run', '--rm', '--network', 'none', '--volumes-from', 'nginx:ro',
                '-v', str(generated) + ':/etc/nginx/security:ro', IMAGE, 'nginx', '-t')
            for name in files:
                prepare_origin.write_private(security / name, (generated / name).read_text())
        # 前回reload失敗の場合も再試行する。失敗時に許可範囲を広げない。
        run('docker', 'exec', 'nginx', 'nginx', '-t')
        run('docker', 'exec', 'nginx', 'nginx', '-s', 'reload')
        if normalize(current['portStates']) != planned:
            payload = staging / 'firewall.json'
            payload.write_text(json.dumps({'instanceName': args.instance, 'portInfos': planned}))
            run(*aws, 'put-instance-public-ports', '--cli-input-json', 'file://' + str(payload))
        after = json.loads(run(*aws, 'get-instance-port-states', '--instance-name', args.instance))
        if normalize(after['portStates']) != planned:
            raise RuntimeError('Firewall verification failed; inspect state before retrying')
    print(f'Synchronized {len(networks)} CloudFront ranges; SSH rules preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--region', default='ap-northeast-1')
    parser.add_argument('--apply', action='store_true')
    arguments = parser.parse_args()
    os.umask(0o077)
    try:
        sync(arguments)
    except Exception as error:
        # AWS例外の本文やコマンド引数は通常ログへ出さない。
        print(f'Origin range synchronization failed: {type(error).__name__}', flush=True)
        log = Path('/home/ec2-user/carbohydratepro/django_debug.log')
        if os.geteuid() == 0 and log.parent.is_dir():
            from datetime import datetime, timezone
            with log.open('a') as stream:
                stamp = datetime.now(timezone.utc).isoformat()
                stream.write(f'ERROR {stamp} origin_ranges 0 0 CloudFront IP範囲の同期に失敗しました。\n')
        raise SystemExit(1) from None
