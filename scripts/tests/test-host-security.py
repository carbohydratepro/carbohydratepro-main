"""ホスト監視の合成データ検証。root・実ホストの変更・ネットワーク走査は不要。"""
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('host_monitor', Path(__file__).parents[1]/'collect-host-security.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class HostMonitorTest(unittest.TestCase):
    def test_baseline_cursor_deduplication_and_reappearance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            watched = root/'watched'
            watched.write_text('reviewed')
            config = root/'config.json'
            config.write_text(json.dumps({'state_dir': str(root/'state'),
                'watch_paths': [str(watched)], 'ssh_users': [], 'ssh_networks': []}))
            config.chmod(0o600)
            original_stat = monitor.Path.stat
            def owned(path, **kwargs):
                info = original_stat(path, **kwargs)
                if path == config:
                    values = list(info)
                    values[4] = 0
                    return os.stat_result(values)
                return info
            entry = {'MESSAGE': 'Accepted publickey for intruder from 198.51.100.1 port 22',
                     '__CURSOR': 'cursor-1', '__REALTIME_TIMESTAMP': str(int(datetime.now(timezone.utc).timestamp()*1000000))}
            calls = []
            def fake_command(args):
                calls.append(args)
                if args[0] == 'ss':
                    return 'tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n'
                return '' if '--after-cursor' in args else json.dumps(entry)
            previous_umask = os.umask(0o077)
            try:
                with patch.object(monitor.os, 'geteuid', return_value=0), patch.object(monitor.Path, 'stat', owned), patch.object(monitor, 'command', side_effect=fake_command):
                    with patch('sys.argv', ['monitor', '--config', str(config), '--initialize']):
                        monitor.main()
                    watched.write_text('unexpected')
                    with patch('sys.argv', ['monitor', '--config', str(config)]):
                        monitor.main()
                        monitor.main()
                        exported = root/'state/export/events.jsonl'
                        events = [json.loads(line) for line in exported.read_text().splitlines()]
                        self.assertEqual(sorted(e['category'] for e in events), ['file_integrity', 'ssh_unexpected_login'])
                        self.assertTrue(any('--after-cursor' in c and 'cursor-1' in c for c in calls))
                        self.assertNotIn('intruder', exported.read_text())
                        self.assertEqual((root/'state/details.jsonl').stat().st_mode & 0o777, 0o600)
                        watched.write_text('reviewed')
                        monitor.main()
                        watched.write_text('unexpected')
                        monitor.main()
                        self.assertEqual(len(exported.read_text().splitlines()), 3)
                        with patch.object(monitor, 'command', side_effect=OSError('fixture error')):
                            with self.assertRaises(SystemExit):
                                monitor.main()
                        self.assertFalse(json.loads((root/'state/export/heartbeat.json').read_text())['healthy'])
            finally:
                os.umask(previous_umask)

    def test_changed_added_deleted_files_and_modes_are_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'authorized_keys';path.write_text('test key');path.chmod(0o644)
            before = monitor.inventory([folder])
            path.write_text('different test key')
            changed = monitor.inventory([folder])
            self.assertNotEqual(before[str(path)], changed[str(path)])
            path.chmod(0o600)
            self.assertNotEqual(changed[str(path)], monitor.inventory([folder])[str(path)])
            path.unlink()
            self.assertNotIn(str(path), monitor.inventory([folder]))
            added = Path(folder)/'new-file';added.write_text('new')
            self.assertIn(str(added), monitor.inventory([folder]))

    def test_upload_signature_and_symlink_do_not_require_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'normal.jpg').write_bytes(b'\xff\xd8image')
            (root/'renamed.jpg').write_bytes(b'\x7fELFfake')
            (root/'script.php').write_bytes(b'not executed')
            (root/'link').symlink_to('/nonexistent')
            self.assertEqual(set(monitor.suspicious_uploads([folder])),
                             {str(root/x) for x in ('renamed.jpg','script.php','link')})

    def test_ss_collects_tcp_udp_ipv6_without_process_arguments(self):
        text='tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\nudp UNCONN 0 0 [::1]:323 [::]:*\n'
        self.assertEqual(monitor.listeners(text), ['tcp:0.0.0.0:22', 'udp:[::1]:323'])

    def test_trusted_and_unexpected_ssh_and_recent_burst(self):
        now = datetime.now(timezone.utc)
        def entry(message, index, old=False):
            stamp=now-timedelta(minutes=10) if old else now
            return {'MESSAGE':message,'__CURSOR':str(index),'__REALTIME_TIMESTAMP':str(int(stamp.timestamp()*1000000))}
        entries=[entry('Accepted publickey for operator from 192.0.2.1 port 22 ssh2',0),
                 entry('Accepted publickey for root from 192.0.2.1 port 22 ssh2',1),
                 entry('Accepted publickey for operator from 198.51.100.1 port 22 ssh2',2)]
        entries += [entry('Failed password for invalid user nobody from 198.51.100.2 port 22 ssh2',i+3) for i in range(20)]
        result=monitor.ssh_events(entries,{'ssh_users':['operator'],'ssh_networks':['192.0.2.0/24']},now)
        categories=[e[2] for e in result]
        self.assertEqual(categories.count('ssh_login'),1)
        self.assertEqual(categories.count('ssh_unexpected_login'),2)
        self.assertEqual(categories.count('ssh_failure'),20)
        self.assertEqual(categories.count('ssh_burst'),1)
        old=[entry('Failed password for nobody from 198.51.100.2 port 22',i,True) for i in range(20)]
        self.assertNotIn('ssh_burst',[e[2] for e in monitor.ssh_events(old,{'ssh_users':[],'ssh_networks':[]},now)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
