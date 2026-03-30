"""アクティビティトラッキングミドルウェア"""
from collections.abc import Callable
from django.http import HttpRequest, HttpResponse

# URL名 -> (page, action, 対象HTTPメソッド) のマッピング
TRACKING_CONFIG: dict[str, tuple[str, str, list[str]]] = {
    # 家計簿
    "expense_list":              ("expenses", "view",   ["GET"]),
    "create_expenses":           ("expenses", "create", ["POST"]),
    "edit_expenses":             ("expenses", "edit",   ["POST"]),
    "delete_expenses":           ("expenses", "delete", ["POST"]),
    "recurring_payment_list":    ("expenses", "view",   ["GET"]),
    "create_recurring_payment":  ("expenses", "create", ["POST"]),
    "edit_recurring_payment":    ("expenses", "edit",   ["POST"]),
    "delete_recurring_payment":  ("expenses", "delete", ["POST"]),
    # タスク
    "task_list":                 ("tasks", "view",   ["GET"]),
    "create_task":               ("tasks", "create", ["POST"]),
    "edit_task":                 ("tasks", "edit",   ["POST"]),
    "delete_task":               ("tasks", "delete", ["POST"]),
    "temp_task_board":           ("tasks", "view",   ["GET"]),
    "temp_task_api":             ("tasks", "create", ["POST"]),
    # メモ
    "memo_list":                 ("memos", "view",   ["GET"]),
    "create_memo":               ("memos", "create", ["POST"]),
    "edit_memo":                 ("memos", "edit",   ["POST"]),
    "delete_memo":               ("memos", "delete", ["POST"]),
    "toggle_memo_favorite":      ("memos", "toggle", ["POST"]),
    # 買うものリスト
    "shopping_list":             ("shopping", "view",   ["GET"]),
    "create_shopping_item":      ("shopping", "create", ["POST"]),
    "edit_shopping_item":        ("shopping", "edit",   ["POST"]),
    "delete_shopping_item":      ("shopping", "delete", ["POST"]),
    "toggle_check_shopping":     ("shopping", "toggle", ["POST"]),
    "clear_checked_shopping":    ("shopping", "delete", ["POST"]),
    "update_shopping_count":     ("shopping", "edit",   ["POST"]),
    # 習慣トラッカー
    "habit_dashboard":           ("habits", "view",   ["GET"]),
    "habit_list":                ("habits", "view",   ["GET"]),
    "create_habit":              ("habits", "create", ["POST"]),
    "edit_habit":                ("habits", "edit",   ["POST"]),
    "delete_habit":              ("habits", "delete", ["POST"]),
    "toggle_habit":              ("habits", "toggle", ["POST"]),
}

# デモページ（未認証ユーザーのGETアクセスのみ記録）
DEMO_URL_NAMES: set[str] = {
    "demo_expenses",
    "demo_tasks",
    "demo_habits",
    "demo_memos",
    "demo_shopping",
    "demo_board",
    "demo_expenses_settings",
    "demo_task_settings",
    "demo_memo_settings",
    "demo_habit_list",
    "demo_recurring_payments",
}

# view アクションはGETのみ記録（ページ閲覧の重複カウント防止）
# 操作系はPOSTかつ成功レスポンス（200/201/302）のみ記録


class ActivityTrackingMiddleware:
    """ページアクセスと操作を自動的にActivityLogへ記録するミドルウェア"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        self._track(request, response)
        return response

    def _track(self, request: HttpRequest, response: HttpResponse) -> None:
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match is None:
            return
        url_name = resolver_match.url_name

        # デモページ: 未認証ユーザーのGETアクセスのみ記録
        if url_name in DEMO_URL_NAMES:
            if request.method == "GET" and response.status_code == 200:
                try:
                    from .models import ActivityLog
                    ActivityLog.objects.create(page="demo", action="view", user=None)
                except Exception:
                    pass
            return

        # 以降は認証済みユーザーのみ対象
        if not request.user.is_authenticated:
            return
        # スーパーユーザー・スタッフは記録しない（自分の操作でデータを汚さないため）
        if request.user.is_superuser or request.user.is_staff:
            return

        if url_name is None or url_name not in TRACKING_CONFIG:
            return

        page, action, methods = TRACKING_CONFIG[url_name]

        # 対象HTTPメソッドでなければスキップ
        if request.method not in methods:
            return

        # 成功レスポンスのみ記録（200, 201, 302）
        if response.status_code not in (200, 201, 302):
            return

        try:
            from .models import ActivityLog
            ActivityLog.objects.create(
                page=page,
                action=action,
                user=request.user,
            )
        except Exception:
            # トラッキング失敗がアプリに影響しないよう例外を抑制
            pass
