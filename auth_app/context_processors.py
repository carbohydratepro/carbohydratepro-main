from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from . import services


def account_switcher(request: HttpRequest) -> dict[str, Any]:
    """ヘッダー用のアカウント切替情報を追加する。"""
    if not request.user.is_authenticated:
        return {
            'account_switcher_memberships': [],
            'account_switcher_other_memberships': [],
        }

    memberships = services.get_account_memberships(request)
    return {
        'account_switcher_memberships': memberships,
        'account_switcher_other_memberships': [
            membership for membership in memberships if membership.user_id != request.user.pk
        ],
    }
