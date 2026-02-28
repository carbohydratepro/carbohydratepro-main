# 完了タスク

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

## factory_boy の導入（テストデータ管理の統一）
- **実装内容**: `requirements.txt` に `factory-boy` を追加。`tests/factories.py` を新規作成し、UserFactory・LoginHistoryFactory・EmailVerificationTokenFactory・PaymentMethodFactory・CategoryFactory・TransactionFactory・RecurringPaymentFactory・TaskLabelFactory・TaskFactory・MemoTypeFactory・MemoFactory・ShoppingItemFactory・ContactMessageFactory の全13クラスを定義。`tests/__init__.py` を追加。全5テストファイル（test_auth.py・test_expenses.py・test_task.py・test_memo.py・test_shopping.py）の setUp() を Factory 記述に移行。`get_user_model()` を使った手書きユーザー生成を `UserFactory()` に置換。他ユーザー生成も `UserFactory()` に簡略化。`client.login(username='test@example.com', ...)` を `client.login(username=self.user.email, ...)` に修正。ハードコードされたメールアドレスのアサーション（`assertIn('test@example.com', str(...))`）を `self.user.email` 参照に修正。全 293 件のテスト通過を確認。
- **実装日時**: 2026-02-28 19:00

## 家計簿：定期的支払いの自動化
- **実装内容**: RecurringPaymentモデルの追加（毎日・毎週・毎月・毎年の頻度設定、曜日・日・月の指定、有効/無効切り替え、実行日追跡）。定期支払いの一覧表示・新規作成・編集・削除・有効/無効切り替え・手動実行のビューとテンプレートを実装。バリデーション付きフォーム（頻度に応じた必須フィールドの制御）。管理コマンド`execute_recurring_payments`による自動実行対応。家計簿一覧画面に定期支払い管理画面へのリンクを追加。テスト77件全てパス。
- **実装日時**: 2026-02-10 01:39

