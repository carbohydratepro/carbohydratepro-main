#!/usr/bin/env python3
"""Root-owned host monitor. Never changes firewall rules or deletes suspicious files."""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess

UTC = timezone.utc


def atomic_json(path, data, mode=0o600):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as out:
        json.dump(data, out, ensure_ascii=False)
        out.flush()
        os.fsync(out.fileno())
    temporary.chmod(mode)
    temporary.replace(path)


def digest_file(path):
    info = path.lstat()
    identity = f'{stat.S_IMODE(info.st_mode)}:{info.st_uid}:{info.st_gid}:'
    if path.is_symlink():
        identity += 'symlink:' + os.readlink(path)
    elif path.is_file():
        # No special devices or FIFO reads; do not follow links swapped during the scan.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as data:
            if not stat.S_ISREG(os.fstat(data.fileno()).st_mode):
                raise ValueError('Not a regular monitored file')
            digest = hashlib.sha256()
            for chunk in iter(lambda: data.read(1024*1024), b''):
                digest.update(chunk)
            identity += digest.hexdigest()
    return hashlib.sha256(identity.encode()).hexdigest()


def inventory(paths):
    result = {}
    for name in paths:
        root = Path(name)
        if not root.is_absolute():
            raise ValueError('Watch paths must be absolute')
        if not root.exists() and not root.is_symlink():
            result[str(root)] = 'missing'
            continue
        result[str(root)] = digest_file(root)
        if root.is_dir() and not root.is_symlink():
            for directory, dirs, files in os.walk(root, followlinks=False):
                for leaf in dirs + files:
                    path = Path(directory) / leaf
                    result[str(path)] = digest_file(path)
    return result


def listeners(text):
    result = set()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[0] in ('tcp', 'udp'):
            result.add(fields[0] + ':' + fields[4])
    return sorted(result)


def suspicious_uploads(roots):
    found = []
    for root in roots:
        for directory, dirs, files in os.walk(root, followlinks=False):
            for leaf in dirs + files:
                path = Path(directory) / leaf
                if path.is_symlink():
                    found.append(str(path))
                    continue
                if not path.is_file():
                    continue
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        continue
                    header = stream.read(64).lstrip()
                if (path.suffix.lower() in {'.py', '.php', '.sh', '.elf', '.so', '.exe', '.pl'}
                        or header.startswith((b'\x7fELF', b'MZ', b'#!', b'<?php'))):
                    found.append(str(path))
    return found


def ssh_events(entries, config, now):
    events = []
    failed = {}
    for item in entries:
        message = str(item.get('MESSAGE', ''))
        occurred = datetime.fromtimestamp(int(item['__REALTIME_TIMESTAMP']) / 1000000, UTC)
        identity = item['__CURSOR']
        accepted = re.search(r'Accepted \S+ for (\S+) from (\S+)', message)
        if accepted:
            user, address = accepted.groups()
            trusted = user in config['ssh_users'] and any(
                ipaddress.ip_address(address) in ipaddress.ip_network(network)
                for network in config['ssh_networks'])
            events.append((identity, occurred, 'ssh_login' if trusted else 'ssh_unexpected_login',
                           'SSH login: ' + user + ' from ' + address))
        failure = re.search(r'(?:Failed \S+ for .*|Invalid user \S+) from (\S+)', message)
        if failure:
            address = failure.group(1)
            events.append((identity, occurred, 'ssh_failure', 'SSH authentication failed from ' + address))
            if occurred >= now-timedelta(minutes=5):
                failed.setdefault(address, []).append(identity)
    for address, identities in failed.items():
        if len(identities) >= 20:
            events.append((identities[-1]+':burst', now, 'ssh_burst', 'SSH burst from '+address))
    return events


def command(args):
    return subprocess.check_output(args, text=True, timeout=45, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='/etc/carbohydratepro/host-monitor.json')
    parser.add_argument('--initialize', action='store_true', help='Create a reviewed baseline; refuses to overwrite')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Run as root')
    os.umask(0o077)
    config_path = Path(args.config)
    info = config_path.stat()
    if info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
        raise SystemExit('Configuration must be root-owned mode 0600')
    config = json.loads(config_path.read_text())
    state_dir = Path(config['state_dir'])
    if not state_dir.is_absolute():
        raise SystemExit('State directory must be absolute')
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_dir.chmod(0o700)
    export = state_dir/'export'
    export.mkdir(mode=0o755, exist_ok=True)
    export.chmod(0o755)
    lock = (state_dir/'monitor.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        return
    now = datetime.now(UTC)
    baseline_path = state_dir/'baseline.json'
    cursor_path = state_dir/'cursor.json'
    try:
        current = {'files': inventory(config['watch_paths']),
                   'listeners': listeners(command(['ss', '-H', '-lntu']))}
        if args.initialize:
            if baseline_path.exists():
                raise ValueError('Baseline exists: review changes explicitly; never auto-accept them')
            atomic_json(baseline_path, current)
            print('Reviewed baseline created. Monitoring has not yet run.')
            return
        baseline = json.loads(baseline_path.read_text())
        events = []
        for path in sorted(set(baseline['files']) | set(current['files'])):
            before = baseline['files'].get(path, 'missing')
            after = current['files'].get(path, 'missing')
            if before != after:
                events.append((f'file:{path}:{after}', now, 'file_integrity', path))
        for endpoint in set(current['listeners'])-set(baseline['listeners']):
            events.append(('listener:'+endpoint, now, 'new_listener', endpoint))
        for path in suspicious_uploads(config.get('upload_roots', [])):
            events.append(('upload:'+path+':'+digest_file(Path(path)), now, 'suspicious_file', path))
        # Read a rolling window as well as the cursor: overlapping failures must count toward bursts.
        cursor = json.loads(cursor_path.read_text()) if cursor_path.exists() else {'last': None, 'bursts': []}
        journal_args = ['journalctl', '-u', 'sshd', '-o', 'json', '--no-pager']
        window = [json.loads(line) for line in command(journal_args + ['--since', '-5 minutes']).splitlines()]
        entries = ([json.loads(line) for line in command(journal_args + ['--after-cursor', cursor['last']]).splitlines()]
                   if cursor['last'] else window)
        # Cursor resumes events after outages; the overlapping window is only for burst detection.
        events += [e for e in ssh_events(entries, config, now) if e[2] != 'ssh_burst']
        bursts = [e for e in ssh_events(window, config, now) if e[2] == 'ssh_burst']
        events += [e for e in bursts if e[0] not in cursor.get('bursts', [])]
        seen_path = state_dir/'seen-findings.json'
        previous = set(json.loads(seen_path.read_text())) if seen_path.exists() else set()
        active = {event[0] for event in events if event[2] not in {'ssh_login', 'ssh_unexpected_login', 'ssh_failure', 'ssh_burst'}}
        fresh = [event for event in events if event[0] not in previous]
        for path, private in [(export/'events.jsonl', False), (state_dir/'details.jsonl', True)]:
            if path.exists() and path.stat().st_size > 5*1024*1024:
                path.replace(path.with_name(path.name+'.1'))
            with path.open('a') as out:
                for identity, occurred, category, detail in fresh:
                    item = {'id': hashlib.sha256((identity+':'+occurred.isoformat()).encode()).hexdigest(),
                            'occurred_at': occurred.isoformat(), 'category': category}
                    if private:
                        item['detail'] = detail
                    out.write(json.dumps(item, ensure_ascii=False)+'\n')
            path.chmod(0o600 if private else 0o644)
        atomic_json(cursor_path, {'last': entries[-1]['__CURSOR'] if entries else cursor['last'],
                                  'bursts': [e[0] for e in bursts]})
        atomic_json(seen_path, sorted(active))
        atomic_json(export/'heartbeat.json', {'checked_at': now.isoformat(), 'healthy': True}, 0o644)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        atomic_json(export/'heartbeat.json', {'checked_at': now.isoformat(), 'healthy': False}, 0o644)
        # No secrets or untrusted journal text in service output.
        raise SystemExit('Host monitor failed; review configuration, files and system journal permissions')
    finally:
        lock.close()


if __name__ == '__main__':
    main()
