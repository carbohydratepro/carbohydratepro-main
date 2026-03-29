# 完了タスク

## 未ログインユーザー用のデモ画面実装
- **実装内容**: `/demo/` URLにアクセスできる `DemoView` を `auth_app/views.py` に追加。Bootstrap タブ形式で家計簿・タスク管理・習慣トラッカー・メモ・買い物リスト・一時タスク（カンバン）の6機能をサンプルデータで閲覧できるデモページ（`registration/demo.html`）を作成。トップページのCTAに「デモを見る」ボタンを追加し、ナビバーにも「デモ」リンクを追加（未ログイン時のみ表示）。
- **実装日時**: 2026-03-27 05:27

## 管理者ユーザーの管理画面を追加
- **実装内容**: `ContactMessage` にstatus（未対応/対応中/対応済み）・admin_reply・admin_reply_atフィールドを追加。`CustomUser` にlast_active_atフィールド追加（EmailVerificationMiddlewareで30分ごとに自動更新）。スタッフ専用の管理パネル（`/carbohydratepro/manage/`）を新設し、①問い合わせ一覧（ステータス・種別フィルタ）②問い合わせ詳細・返信（メール送信オプション付き）③ユーザー統計（Chart.jsによる日別/月別グラフ・認証済みのみ切り替え・累計/新規の2軸表示・最近のユーザー一覧）を実装。ヘッダーにスタッフのみ表示される「管理」リンクを追加。テスト13件全通過。
- **実装日時**: 2026-03-24 11:26

## 一時タスク画面で複数セットを切り替えるようにする
- **実装内容**: `TempTaskSet` モデルを追加し `TempTaskItem` にFKを追加。セット一覧/作成/更新/削除のAPIを追加。タスクAPIはset_idでフィルタリング。UIはタブ形式のセット切り替え（ダブルクリックでリネーム、長押しで削除）と「+」ボタンによるセット追加。初回アクセス時に「デフォルト」セットを自動作成し既存タスクを割り当て。前回のセット選択はlocalStorageで永続化。テスト19件全通過。
- **実装日時**: 2026-03-24 11:13

## 全体的な操作方法の改善
- **実装内容**: 一時タスク画面（カンバンボード）の操作方法を刷新。①削除ボタン（×）を廃止し、長押し（500ms）でカード上に赤いゴミ箱オーバーレイを表示→タップで削除、3秒後に自動キャンセル、Escapeキー/外側クリックでもキャンセル、モバイルではバイブレーションフィードバック。②デスクトップ（768px以上）ではドラッグ時にカラムに直接ドロップしてステータス変更し、薄赤の削除ゾーンをボード下部に表示。③モバイル（縦並び）では既存の5ゾーンオーバーレイを維持。ダブルクリック/タップでの編集は引き続き有効。テスト13件全通過。
- **実装日時**: 2026-03-16 22:07

## 一時タスク画面の改修
- **実装内容**: LocalStorageによる揮発管理からサーバーDB永続化（非同期API）に移行。`TempTaskItem` モデル（user, title, status, order, created_at, updated_at）を追加し、マイグレーション0026を適用。REST APIエンドポイント4本（一覧取得・作成・更新・削除・全削除）をDjangoビューに追加し、URLに登録。TypeScriptを全面書き換え: ローカル状態（`localId`/`serverId`/`savedState`）で楽観的UI更新を実現し、非同期保存中は橙色パルスドット、保存失敗時は赤ドットをカードに表示。既存のドラッグ&ドロップ・タッチ操作・インライン編集はそのまま維持。CSSに `saving`/`save-error` クラスと `unsaved-pulse` アニメーションを追加。テスト13件（既存3件+新規10件）全通過。
- **実装日時**: 2026-03-15 22:39

## トップ画面の改修
- **実装内容**: ①ログイン済みユーザーのCTAを「家計簿へ」から「マイページへ」に変更。②各画面（家計簿・タスク管理・メモ・習慣トラッカー・買い物リスト・一時タスク）の説明カードを追加。③更新履歴をシンプルなリスト形式に変更し、max-height: 180px でスクロール表示に。④done.md の内容をもとに更新履歴を最新化（粒度は月単位）。
- **実装日時**: 2026-03-15 00:00

## マイページ画面の改善
- **実装内容**: マイページに「各画面の設定」セクションを追加し、家計簿・タスク管理・メモの各設定ページへのリンクカードを一覧表示。また「お問い合わせ」セクションを追加し、お問い合わせフォームへのリンクを設置。
- **実装日時**: 2026-03-15 00:00

## 家計簿の機能拡張
- **実装内容**: ①年選択: 月/年切替ボタンを追加し、年モードでは年全体の取引を表示。月別収支グラフ（grouped bar chart）で各月の収入・支出を可視化。②カード並べ替え: 絞り込みエリアに並べ替え選択を追加（日付新しい順・古い順・金額高い順・低い順）。`selectors.get_transactions` に `sort_by` パラメータを追加。
- **実装日時**: 2026-03-15 19:34

## タスク管理画面の改善
- **実装内容**: カードの一覧表示・検索フィルター・ページネーションを削除し、カレンダー表示（月ビュー）とガントチャート表示（日ビュー）のみに整理。`task_list` ビューから不要な `Paginator`・検索クエリ・フィルター処理を削除しシンプル化。
- **実装日時**: 2026-03-15 09:25

## 習慣トラッカーの改善
- **実装内容**: ①iPhoneでのスワイプ誤作動修正: `isCardDragging`フラグを追加し、カード横スワイプ中にパネル（日/週/年）が切り替わらないよう対策。②カード縦幅圧縮: padding/font-sizeを削減しカードを小型化。③習慣一覧を別画面(`/carbohydratepro/habits/list/`)に分離し、ダッシュボードに「習慣を管理」リンクを追加。週ビューの日付ヘッダー・年ビューのヒートマップセルクリックで達成詳細をパネル下部に表示する`showDayDetail()`機能を実装。`habit_status_json`の7日制限を撤廃し過去全日付に対応。④年表示の月ラベルバグ修正: 年指定モード時に対象年外（前年12月）のセルで月ラベルを記録しないよう修正し「De2026/Jan」のような誤表示を解消。テスト31件全通過。
- **実装日時**: 2026-03-11 00:00

## バグ修正
- **実装内容**: ①Django 5.2では`LogoutView`がGETリクエストを受け付けないため、両ヘッダー（`app/templates/app/_header.html`、`auth_app/templates/registration/_header.html`）のログアウトリンクを`<a href>`からCSRFトークン付きPOSTフォームに変更。②`registration/_header.html`のログイン済みメニューに「一時タスク」（`temp_task_board`）と「習慣」（`habit_dashboard`）リンクが欠落していたため追加。
- **実装日時**: 2026-03-11 00:00

## 習慣リストの改善
- **実装内容**: ①フォームの並び順を「種別→頻度→係数→目標」に変更し、週/月目標は選択した頻度のときのみ表示するよう動的切替を実装。②過去7日間の日付ナビゲーションボタンを追加し、選択日のAJAX読み込みで当日以外の実績も確認・編集可能に。③習慣カードに係数スライダーを追加し、達成登録時に係数を上書きできるように変更（HabitRecordにcoefficientフィールド追加）。④HabitRecordに`created_at`（登録日時）を追加（画面には非表示）。⑤年ビューにJan〜Decの月ラベル表示、直近/年別選択ボタン、年別ヒートマップAJAXロードを実装。記録あり・スコア0のセルを薄い黄色（#fffde7）で表示。⑥習慣の追加/編集後の成功ポップアップを削除。⑦習慣を日→週→月の頻度順でソート。⑧セレクター・ビュー・TypeScript・テストを全面更新。テスト28件全通過。
- **実装日時**: 2026-03-04 21:55

## 習慣トラッカーの修正
- **実装内容**: ①スライダー操作中はカードスワイプを無効化（`isSliderInteraction()`チェック追加）。②縦スクロール中はカードが横にスライドしないよう`isVertical`フラグで方向ロックを実装。③-1日/-2日ボタンを廃止し`<input type="date" min max>`のdate pickerに変更、AJAX読み込みに対応。④パネル切替・日付変更・年ビューロード後に`updateWrapHeight()`でパネルラッパーの高さを動的更新し、余白が生じないよう対応。⑤年ビューのヒートマップセルホバー時スコアを整数表示（Math.round）＋カンマなしに修正。⑥年ビューのAJAX読み込みにtry/catchエラー処理を追加し、直近以外の年でもグラフが表示されるよう修正。テスト28件全通過。
- **実装日時**: 2026-03-05 02:20

## 習慣トラッカーの修正（追加修正）
- **実装内容**: ①カードは完了状態に応じた方向のみスライド可能に制限（完了済み→左のみ、未完了→右のみ）。②`.habit-panels`に`align-items: flex-start`を追加し、パネル間で高さが影響し合う問題を解消。③`USE_THOUSAND_SEPARATOR=True`設定により年数が"2,025"と表示されていた問題を`|stringformat:"d"`フィルターで修正（ボタンのdata属性と表示テキスト、JavaScriptのhabitSelectedYear変数）。④同カンマ問題により`parseInt("2,025")`=2となり年別ヒートマップが表示されなかった根本原因を解消。JavaScriptにも`replace(/,/g, '')`の防御的処理を追加。
- **実装日時**: 2026-03-05 02:40

## 習慣トラッカーUIの改善
- **実装内容**: 習慣トラッカーのUI・モデルを全面改修。①モデル: `color`フィールド削除、`coefficient`をFloatField→PositiveSmallIntegerField(1〜10)に変更、`is_positive`(良/悪判定)・`weekly_goal`・`monthly_goal`フィールドを追加、`signed_coefficient`プロパティと`color`プロパティを実装。②データ移行: マイナス係数を`is_positive=False`+絶対値に変換するRunPythonマイグレーション追加。③UI: 日/週/年の3パネルスライダー（タブクリック+横スワイプで切替）に変更。④日ビュー: 未達成/達成済みの2エリア分割、カードを右スワイプで達成・左スワイプで未達成に変更するジェスチャー操作（タッチ&マウス対応）。⑤週ビュー: 7日グリッドで習慣別の達成ドット+週目標達成バッジを表示。⑥フォーム: 緑/赤ボタンで良い/悪い習慣を選択、係数は1〜10の正整数入力、週/月目標回数フィールド追加、新規追加・編集ともモーダルで実施。テスト16件全通過。
- **実装日時**: 2026-03-03 15:10

## タスク完了を可視化する
- **実装内容**: 習慣トラッカー機能を新規実装（`app/habit/` サブモジュール）。`Habit`（習慣）と `HabitRecord`（達成記録）モデルを追加。GitHub contribution graph 風のヒートマップ（52週×7日グリッド、スコアに応じた緑/赤グラデーション）をTypeScript/DOMで描画。毎日/毎週/毎月の頻度設定、プラスマイナス係数（良い習慣=プラス、悪い習慣=マイナス）、1タップで当日の達成/未達成をAJAXトグル。ナビに「習慣」リンクを追加。テスト11件追加。
- **実装日時**: 2026-03-03 11:45

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


## 軽微なバグの修正&改善
- **実装内容**: ①「タスク管理」の文言を「スケジュール」に統一（`task/list.html`）。②タスク保存時の時刻がUTC（米国時間）で表示されるバグを修正 — `forms.py` の時刻初期値設定に `timezone.localtime()` を使用してJST変換。③日付・時刻入力フィールドをクリックした際に必ずピッカーが開くよう `showPicker()` を呼ぶ共通初期化関数 `initDateTimePickers()` を `app.ts` に追加（モーダル表示後にも適用）。
- **実装日時**: 2026-03-20 03:15

## 微修正（収支登録ボタン・iアイコン・ログインリダイレクト・カレンダー前後月表示）
- **実装内容**: ①家計簿画面の「新規登録」ボタンを「収支登録」に変更。②家計簿・スケジュール・メモ・買い物リスト・習慣一覧の各画面のタイトル横にiアイコンを追加し、クリックでBootstrap collapseによる画面説明を表示。③ログイン済みユーザーがログイン画面にアクセスした場合、`redirect_authenticated_user = True` でトップ（ホーム）画面に自動リダイレクト。④タスクカレンダーの前後月セルに実際の日付を表示（monthdatescalendar使用）し、クリックでタスク追加・閲覧が可能に。前後月セルはfaded表示（背景薄灰・opacity 0.7）。タスク取得範囲を前後7日分拡張してカレンダー端のタスクも正しく表示。
- **実装日時**: 2026-03-22 02:40

## バグ修正/機能改善（買い物リストモバイルスクロール・お問い合わせ全文表示・家計簿グラフ配色固定・棒グラフ土日色付け）
- **実装内容**: ①買い物リストモバイル対応：Bootstrap 4の`modal-dialog-scrollable.modal-dialog-centered`組み合わせ時に`modal-content`の`max-height`がnoneになるバグをCSS上書きで修正（`shopping.css`）。②お問い合わせ全文表示：履歴一覧で30語以上のメッセージに「全文を見る/閉じる」トグルを追加（Bootstrap collapseとJS）、`contact.html`・`contact.css`を更新。③家計簿カテゴリグラフ配色固定：カテゴリIDのmod割り当てで同一カテゴリが常に同じ色で表示されるよう`selectors.py`を修正、パレットを5色→15色に拡張（`utils.py`）。④棒グラフ土日色付けトグル：日別支出棒グラフに「土日色付け」ボタンを追加（PC/モバイル両対応）、ON時に土曜・日曜のバーをオレンジ色で表示、状態はlocalStorageに永続化（`transaction.ts`・`list.html`）。
- **実装日時**: 2026-03-22 21:00
