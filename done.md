# 完了タスク

## メンテナンスモードを実装する
- **実装内容**: `MaintenanceModeMiddleware` を `project/middleware.py` に追加。`MAINTENANCE_MODE` 環境変数（デフォルト `False`）が `True` の場合、スタッフ以外のすべてのリクエストに HTTP 503 でメンテナンスページを返す。静的ファイルはメンテナンス中でも通過する。メンテナンスページ（`templates/maintenance.html`）はスタンドアロン HTML でFont Awesome アイコン・アニメーション・ユーモアのあるコメント付き。`project/settings/base.py` の `MIDDLEWARE` に追加。テスト4件を `project/tests/test_middleware.py` に追加。
- **実装日時**: 2026-03-03 10:30

## 家計簿グラフの折れ線グラフのホバーアクションを有効にする
- **実装内容**: Chart.js v4 の折れ線グラフ（日別収支推移）にホバーアクションを実装。`interaction: { mode: 'index', intersect: false }` を追加することで、ポイント非表示（pointRadius: 0）の状態でもマウスホバー時にツールチップが表示されるように修正。`plugins.tooltip.callbacks.label` をカスタマイズして「ラベル: ¥金額円」形式で表示し、基準線（0円）はツールチップから除外。`globals.d.ts` に `interaction`・`ChartTooltipCallbacks`・`ChartTooltipContext` の型定義を追加。PC/モバイル両グラフに適用。
- **実装日時**: 2026-03-01 06:00

## 一時タスク画面の実装
- **実装内容**: カンバンボード型の一時タスク画面に2つの機能を追加。①インライン編集：ダブルクリック（PC）またはダブルタップ（モバイル、300ms以内）でタスクをテキスト入力欄に切り替えて編集可能。Enterで保存、Escapeでキャンセル、フォーカス外れで保存。②5ゾーンドラッグオーバーレイ：ドラッグ開始時に全画面オーバーレイを表示し、「未着手」「進行中」「終了」「削除」「キャンセル」の5ゾーンを提示。PCはHTML5 Drag & Drop（requestAnimationFrameでドラッグ画像キャプチャ後に表示）、モバイルはタッチイベント（8px移動でドラッグ検出）に対応。既存のゴミ箱エリアを削除し、オーバーレイに集約。TypeScript/CSS/HTMLを修正し、テスト3件全通過。
- **実装日時**: 2026-03-01 03:55

## jsファイルをts運用に変える
- **実装内容**: 8つのJSファイル（app.js, label-settings.js, markdown-lite.js, memo.js, shopping.js, task.js, transaction.js, temp_task.js）をTypeScriptに移行。`src/ts/` をTypeScriptソースディレクトリとして新設。`tsconfig.json`（target: ES2017, module: none, strict: true）と `src/ts/globals.d.ts`（Chart.js CDN型定義・Bootstrap 4 jQuery modal拡張・Window拡張・グローバル変数宣言）を作成。全ファイルに型アノテーションを付与し、`instanceof HTMLFormElement` によるDOM型の安全な絞り込み、ジェネリクス付き `querySelectorAll<HTMLElement>()` 等のTypeScriptイディオムを適用。`npm install && npm run build` でエラーなしにコンパイル完了。`biome.json` にコンパイル済みJSを除外設定追加、`.gitignore` に `node_modules/` 追加、`CLAUDE.md` にTypeScriptコーディング規約を追記。
- **実装日時**: 2026-03-01 02:30

## 監視スクリプトの状態確認と改善
- **実装内容**: 監視スクリプト（check_security_log, check_debug_log）の状況を確認し、Docker環境に統合。ホスト環境にcronがインストールされておらず、監視スクリプトが過去に一度も実行されていないことを確認。crontabにセキュリティログ監視（1分ごと）とデバッグログ監視（5分ごと）を追加。SECURITY_MONITORING_SETUP.mdをDocker環境向けに全面改訂（Windows環境の記述を削除、Docker環境での手動テスト方法を追記、トラブルシューティングをDocker向けに更新）。非推奨のcheck_security.sh/batと不要なbatファイル（check_security_only.bat, check_debug_only.bat）をすべて削除。スクリプトファイルに実行権限を付与。Docker管理方式を推奨実装として確定。
- **実装日時**: 2026-02-15 19:07

## 家計簿機能の定期支払仕様変更
- **実装内容**: 定期支払いをcronで自動実行する仕組みを実装。本番環境・ローカル環境の両方にcronサービスを追加（docker-compose.yml、docker-compose-dev.yml）。Dockerfile.cronとcrontabファイルを作成し、毎日0時に自動実行されるよう設定。CRON_SETUP.mdを作成してcron設定の詳細と手動テスト方法を記載。定期支払い画面（recurring_list.html）から手動実行ボタンを削除し、自動実行される旨の説明を追加。views.pyとurls.pyから手動実行用のexecute_recurring_paymentsビュー・URL設定を削除。本番環境への変更ルール（.claude/rules/production.md）を追加。
- **実装日時**: 2026-02-15 02:14

## タスク管理機能の改善
- **実装内容**: タスク管理機能の詳細テストを実施。11個の新規テストケースを追加（繰り返しタスクの子タスク生成テスト、開始日なしの繰り返しタスクテスト、親タスク削除時のカスケード削除テスト、繰り返しタスク更新時の子タスク再生成テスト、毎週・毎月繰り返しタスクの日付テスト、終了日時が開始日時より前の場合のバリデーションテスト、終日タスクの時刻設定テスト、繰り返しタスクで間隔なしのバリデーションテスト）。views.py、forms.py、models.pyに型アノテーションを追加してCLAUDE.mdのルールに準拠。JavaScriptコードが`var`を使用していないことを確認。全52個のテストが成功。バグは発見されず、テストカバレッジと型安全性を大幅に向上。
- **実装日時**: 2026-02-12 02:15

## 一時タスク管理機能を搭載する
- **実装内容**: LocalStorageを使用したカンバンボード型の一時タスク管理機能を実装。3カラム構成（「やること」/「やってる」/「できた」）でPC・モバイル両対応。HTML5 Drag & DropによるPCでのドラッグ&ドロップ操作、タッチイベントによるモバイルでのドラッグ操作に対応。ゴミ箱エリアへのドラッグで削除、×ボタンでの個別削除、全削除ボタンを実装。データはLocalStorageに保存（サーバー不要）。ナビゲーションに「一時タスク」リンクを追加。新規ビュー（temp_task_board）・URL（/tasks/board/）・テンプレート・CSS・JSを追加。テスト3件追加（未ログイン時リダイレクト、ログイン時アクセス可能、テンプレート確認）。
- **実装日時**: 2026-02-20 00:00

## 設定ファイルの分割
- **実装内容**: `project/settings.py` を `project/settings/` ディレクトリに分割。`base.py`（全環境共通）・`development.py`（開発用: DEBUG=True, SITE_PROTOCOL=http）・`production.py`（本番用: DEBUG=False, セキュリティヘッダー有効）・`test.py`（テスト用: locmemメール, MD5パスワードハッシュで高速化）の4ファイル構成に変更。旧 settings.py の LOGGING 重複定義（django.core.mail）を修正。`manage.py` のデフォルトを `project.settings.development`、`wsgi.py` のデフォルトを `project.settings.production` に更新。`docker-compose-dev.yml` の gunicorn・cron サービスに `DJANGO_SETTINGS_MODULE=project.settings.development` を明示設定。テストは `python manage.py test --settings=project.settings.test` で実行可能。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-27 22:40

## auth_app/signals.py の整理（Service 層への集約）
- **実装内容**: `auth_app/services.py` を新規作成し、`get_client_ip`・`get_location_from_ip` をユーティリティ関数として移動。`create_default_user_data`（デフォルトデータ生成）・`record_login_success`（ログイン成功処理）・`record_login_failure`（ログイン失敗処理）・`notify_admin_login`（管理者ログイン通知）を実装。`auth_app/signals.py` をサービス呼び出しの薄いラッパーに整理し、`create_default_payment_method_and_category` のシグナルを削除。`auth_app/views.py` の `Signup.form_valid()` で `services.create_default_user_data(user)` を明示的に呼び出す形に変更。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-28 20:56

## Service + Selector パターン導入: memo / shopping
- **実装内容**: `app/memo/selectors.py` を新規作成（`get_memo_types`・`get_memos`）。`app/memo/services.py` を新規作成（`ensure_default_memo_types` を `views.py` から移動）。`app/memo/views.py` を薄くし不要なimport（`django.db.models`・`Q`）を削除。`app/shopping/selectors.py` を新規作成（`get_shopping_items`・`get_one_time_items`・`get_recurring_items`）。`app/shopping/services.py` を新規作成（カウント増減ロジックを `update_item_count` として `views.py` から移動）。`app/shopping/views.py` を薄くし不要なimport（`Q`）を削除。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-28 20:51

## Service + Selector パターン導入: tasks
- **実装内容**: `app/task/selectors.py` を新規作成し、クエリ・データ生成ロジックを `task_list` ビュー（201行）から切り出し（`get_day_view_tasks`・`apply_filters`・`build_gantt_data`・`get_all_user_tasks`・`get_month_tasks`・`build_calendar_data`・`build_task_api_json`・`get_labels`）。`app/task/services.py` を新規作成し、`create_recurring_tasks` を `views.py` から移動。`views.py` を 451行→191行に圧縮し、セレクター・サービスを呼び出す薄い形に変更。`test_task.py` の `create_recurring_tasks` インポートを `views` → `services` に更新。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-28 19:20

## Service + Selector パターン導入: expenses
- **実装内容**: `app/expenses/selectors.py` を新規作成し、クエリ・集計・グラフデータ生成ロジックを `expenses_list` ビュー（180行）から切り出し（`get_date_range`・`get_transactions`・`get_summary`・`build_category_chart_data`・`build_major_category_chart_data`・`build_daily_chart_data`・`get_payment_methods`・`get_categories`・`get_recurring_payments`）。`app/expenses/services.py` を新規作成し、ビジネスロジックを切り出し（`PAYMENT_METHOD_LIMIT`・`CATEGORY_LIMIT` 定数、`is_payment_method_limit_reached`・`is_category_limit_reached`・`execute_recurring_payment`）。`RecurringPayment.execute()` モデルメソッドを `services.execute_recurring_payment()` に移動・削除。`views.py` を 381行→196行に圧縮し、セレクター・サービスを呼び出す薄い形に変更。管理コマンド `execute_recurring_payments` を service 呼び出しに更新。テストの `recurring.execute()` を `services.execute_recurring_payment()` に更新。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-28 19:10

## すべてのpythonファイルに型をつける
- **実装内容**: プロジェクト全体のPythonファイルに型アノテーションを追加。対象ファイル: `app/memo/views.py`・`app/shopping/views.py`・`app/expenses/views.py`・`app/views.py`（全ビュー関数に `HttpRequest`/`HttpResponse`/`JsonResponse` の戻り値型を追加）。`auth_app/forms.py`・`app/memo/forms.py`・`app/shopping/forms.py`・`app/expenses/forms.py`・`app/forms.py`（`__init__`メソッドに `*args: Any, **kwargs: Any -> None`、`clean_*`メソッドに戻り値型を追加）。`auth_app/middleware.py`（`Callable[[HttpRequest], HttpResponse]`型のget_responseパラメータ、各メソッドの戻り値型）。`auth_app/admin.py`（`short_user_agent`・`is_valid_display`・`has_add_permission`・`has_delete_permission`に型追加）。`auth_app/templatetags/filters.py`・`app/templatetags/app_filters.py`（フィルター関数に型追加）。`auth_app/models.py`・`app/memo/models.py`・`app/shopping/models.py`・`app/expenses/models.py`・`app/models.py`（`__str__`・`save`・`is_valid`メソッドに型追加）。`project/middleware.py`（ミドルウェアに型追加）。管理コマンド2件（`handle`・`send_*`メソッドに型追加）。Djangoシステムチェックで問題なし確認。
- **実装日時**: 2026-03-01 03:16

## factory_boy の導入（テストデータ管理の統一）
- **実装内容**: `requirements.txt` に `factory-boy` を追加。`tests/factories.py` を新規作成し、UserFactory・LoginHistoryFactory・EmailVerificationTokenFactory・PaymentMethodFactory・CategoryFactory・TransactionFactory・RecurringPaymentFactory・TaskLabelFactory・TaskFactory・MemoTypeFactory・MemoFactory・ShoppingItemFactory・ContactMessageFactory の全13クラスを定義。`tests/__init__.py` を追加。全5テストファイル（test_auth.py・test_expenses.py・test_task.py・test_memo.py・test_shopping.py）の setUp() を Factory 記述に移行。`get_user_model()` を使った手書きユーザー生成を `UserFactory()` に置換。他ユーザー生成も `UserFactory()` に簡略化。`client.login(username='test@example.com', ...)` を `client.login(username=self.user.email, ...)` に修正。ハードコードされたメールアドレスのアサーション（`assertIn('test@example.com', str(...))`）を `self.user.email` 参照に修正。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-28 19:00

## タスク管理画面のバグ修正
- **実装内容**: `src/ts/task.ts` を修正し以下を実装。①エラーメッセージの詳細表示：AJAXフォーム送信失敗時に、サーバーから返ったエラーをフィールド別に表示（フィールド固有エラーはフィールドの隣、非フィールドエラーはモーダル上部のアラートで表示）。関数名は `displayTaskFormErrors`（`transaction.ts` の `displayFormErrors` との重複を回避）。②時刻フィールドを5分刻みのセレクトボックスに変換：`initializeTimeSelects()` で `<input type="time">` を `<select>` に置き換え、00:00〜23:55 を5分刻みで選択可能に。③デフォルト時刻の設定：新規作成時に開始時刻=現在時刻（5分丸め）、終了時刻=1時間後をデフォルト設定（`setDefaultTimes()`）。④開始日変更時の終了日の自動連動：`handleStartDateChange()` で前回の開始日から期間差を維持したまま終了日を更新。⑤終了日ピッカーの自動オープン：開始日選択後に `showPicker()` / `focus()` で終了日入力を自動フォーカス。⑥開始日時＞終了日時の自動修正：`validateAndFixDateTimeOrder()` で開始日時が終了日時を超えた場合、終了日＝開始日・終了時刻＝開始時刻＋1時間に自動修正。TypeScriptコンパイル（`npm run build`）後、コンテナを再起動して反映。
- **実装日時**: 2026-03-01 13:32

## 家計簿：定期的支払いの自動化
- **実装内容**: RecurringPaymentモデルの追加（毎日・毎週・毎月・毎年の頻度設定、曜日・日・月の指定、有効/無効切り替え、実行日追跡）。定期支払いの一覧表示・新規作成・編集・削除・有効/無効切り替え・手動実行のビューとテンプレートを実装。バリデーション付きフォーム（頻度に応じた必須フィールドの制御）。管理コマンド`execute_recurring_payments`による自動実行対応。家計簿一覧画面に定期支払い管理画面へのリンクを追加。テスト77件全てパス。
- **実装日時**: 2026-02-10 01:39

