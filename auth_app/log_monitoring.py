"""セキュリティ・エラーログの日次集計を支援する。"""

import re
from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path


LOG_TIMESTAMP_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
SECURITY_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("privileged_login", "特権ユーザーログイン検知"),
    ("unknown_login", "存在しないユーザーへのログイン試行"),
    ("locked_login", "ロック中アカウントへのログイン試行"),
    ("admin_probe", "admin access attempt"),
    ("csrf", "CSRF"),
    ("forbidden", "Forbidden"),
)


def log_paths(base_dir: Path, filename: str) -> list[Path]:
    """現在ログと番号付きローテーションログを古い順で返す。"""
    rotated = sorted(
        base_dir.glob(f"{filename}.[0-9]*"),
        key=lambda path: path.stat().st_mtime,
    )
    current = base_dir / filename
    if current.exists():
        rotated.append(current)
    return rotated


def recent_log_lines(paths: Iterable[Path], start: datetime, end: datetime) -> list[str]:
    """指定期間に含まれるタイムスタンプ付きログ行を返す。"""
    lines: list[str] = []
    for path in paths:
        try:
            with path.open(encoding="utf-8", errors="replace") as log_file:
                for raw_line in log_file:
                    match = LOG_TIMESTAMP_PATTERN.search(raw_line)
                    if match is None:
                        continue
                    try:
                        logged_at = datetime.strptime(  # noqa: DTZ007 - ログ自体がJSTのnaive値
                            match.group(1),
                            "%Y-%m-%d %H:%M:%S",
                        )
                    except ValueError:
                        continue
                    if start <= logged_at <= end:
                        lines.append(raw_line.strip())
        except OSError:
            continue
    return lines


def classify_security_logs(lines: Iterable[str]) -> Counter[str]:
    """1行を重複計上せず、日次レポート用カテゴリへ分類する。"""
    counts: Counter[str] = Counter()
    for line in lines:
        lowered = line.lower()
        category = "other"
        for candidate, marker in SECURITY_CATEGORIES:
            if marker.lower() in lowered:
                category = candidate
                break
        counts[category] += 1
    return counts


def actionable_details(security_lines: Iterable[str], debug_lines: Iterable[str]) -> list[str]:
    """メール本文へ載せる重要イベントだけを抽出する。"""
    details = [
        line for line in debug_lines if line.startswith(("CRITICAL", "ERROR"))
    ]
    details.extend(
        line for line in security_lines if "特権ユーザーログイン検知" in line
    )
    return details
