"""AWS公式IP範囲の保存ファイルからNginx用設定を生成する。AWS・本番は変更しない。"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import secrets
import tempfile
from pathlib import Path


def cloudfront_networks(document: dict[str, list[dict[str, str]]]) -> list[str]:
    networks: list[str] = []
    for section, key, version in [('prefixes', 'ip_prefix', 4), ('ipv6_prefixes', 'ipv6_prefix', 6)]:
        for entry in document[section]:
            if entry['service'] != 'CLOUDFRONT_ORIGIN_FACING':
                continue
            network = ipaddress.ip_network(entry[key])
            if network.version != version or network.prefixlen == 0:
                raise ValueError('Invalid CloudFront origin network')
            networks.append(str(network))
    if not networks or not any(':' not in network for network in networks):
        raise ValueError('CloudFront origin IPv4 ranges are missing')
    return sorted(set(networks))


def write_private(path: Path, value: str) -> None:
    """生成途中の設定が読まれないように同じディレクトリで置換する。"""
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.origin-')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prepare(ip_ranges: Path, output: Path) -> None:
    networks = cloudfront_networks(json.loads(ip_ranges.read_text()))
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    if output.is_symlink():
        raise ValueError('Output directory must not be a symbolic link')
    output.chmod(0o700)
    token_file = output / 'origin-token'
    if token_file.is_symlink():
        raise ValueError('Token file must not be a symbolic link')
    token = token_file.read_text().strip() if token_file.exists() else secrets.token_hex(32)
    if not re.fullmatch(r'[0-9a-f]{64}', token):
        raise ValueError('Existing origin token is invalid; no token was rotated')
    write_private(token_file, token + '\n')
    write_private(output / 'origin-token.map', '"' + token + '" 1;\n')
    write_private(output / 'cloudfront-realip.conf', ''.join(
        'set_real_ip_from ' + network + ';\n' for network in networks
    ))
    write_private(output / 'cloudfront-peers.conf', ''.join(
        network + ' 1;\n' for network in networks
    ))
    print(f'Prepared {len(networks)} CloudFront origin ranges in {output}; token not displayed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ip-ranges', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.ip_ranges, args.output_dir)
