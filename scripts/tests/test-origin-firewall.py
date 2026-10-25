"""自動更新によるSSH消失・意図しないポート開放・ルール超過を防ぐ。"""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('sync_origin', Path(__file__).resolve().parents[1] / 'sync-origin-ranges.py')
sync_origin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_origin)


class FirewallTests(unittest.TestCase):
    def setUp(self):
        self.ports = [
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22,
             'cidrs': ['192.0.2.1/32'], 'cidrListAliases': ['lightsail-connect']},
            {'protocol': 'tcp', 'fromPort': 443, 'toPort': 443, 'cidrs': ['203.0.113.0/24']},
        ]
        self.ranges = ['198.51.100.0/25', '198.51.100.128/25', '2001:db8::/32']

    def test_preserves_ssh_and_collapses_only_adjacent_ranges(self):
        plan = sync_origin.firewall_plan(self.ports, self.ranges)
        self.assertEqual(plan[0], sync_origin.normalize(self.ports)[0])
        self.assertEqual(plan[1]['cidrs'], ['198.51.100.0/24'])
        self.assertEqual(plan[1]['ipv6Cidrs'], ['2001:db8::/32'])

    def test_refuses_initial_or_transition_firewall(self):
        for ports in [self.ports[:1], self.ports + [dict(self.ports[1], fromPort=8000, toPort=8000)]]:
            with self.assertRaises(ValueError):
                sync_origin.firewall_plan(ports, self.ranges)

    def test_refuses_worldwide_access_and_missing_family(self):
        for ranges in [self.ranges[:2], self.ranges + ['0.0.0.0/0'], ['::/0', '192.0.2.0/24']]:
            with self.assertRaises(ValueError):
                sync_origin.firewall_plan(self.ports, ranges)
        self.ports[0]['cidrs'] = ['0.0.0.0/0']
        with self.assertRaises(ValueError):
            sync_origin.firewall_plan(self.ports, self.ranges)

    def test_refuses_rule_limit_overflow(self):
        ranges = [f'198.51.100.{n * 2}/32' for n in range(60)] + ['2001:db8::/32']
        with self.assertRaises(ValueError):
            sync_origin.firewall_plan(self.ports, ranges)


if __name__ == '__main__':
    unittest.main()
