# Active Context

## 現在の作業

`task.md` の機能修正（2026-07-26）に対応し、家計簿・スケジュール・スマホ表示・ホームを改善した。

## 機能修正（2026-07-26）

- 家計簿にカテゴリ・支払方法の複数条件と除外条件を追加し、条件とページネーションをURLで維持する。同一種別はOR、カテゴリと支払方法はAND、除外はNOTとした。
- カテゴリ・費用タイプ・日別・年間グラフのクリックから対応する条件へ絞り込む。日別線の名称は「収支」へ統一した。
- カテゴリ・支払方法・タスクラベルに表示順（migration 0037）を持たせ、登録順を初期値としつつ設定画面の矢印で並べ替え可能にした。編集は行のダブルクリックと鉛筆ボタンの両方に対応する。
- タスク設定の週開始を明示的な保存操作にし、ラベルを新規タスクの既定値に選択できるようにした。
- 金額を折り返さず、8桁以上はスマホで文字を小さくする共通表示を家計簿・予算・定期支払い・ホームに適用した。
- ホームに今日の簡易情報と、ボタン操作後にだけ位置情報を使うOpen-Meteoの天気を追加した。
- 検証: 追加Django 11件、関連Django 166件、`npm run check`、migration差分確認は成功。Dockerデーモン停止中のためPostgreSQL・Playwrightは未実行。

## 料理記録（2026-07-26）

- `/carbohydratepro/cooking/` に一覧・検索・並べ替え、登録、編集、詳細画面を追加した。
- `CookingDish`、`CookingStep`、`CookingHistory`（migration 0036）で、料理写真5枚、最大10手順と各2枚の写真、日別の作成回数を管理する。
- 詳細画面はノート形式で手順を1ページずつ表示し、前後ボタンと左右スワイプに対応する。「今日作った」で当日の回数を加算でき、日別履歴の追加・編集・削除も可能。
- JPEG・PNG・WebP、1枚5MB、1送信80MBを検証し、保存先はユーザー別のランダムファイル名とした。Nginxの送信上限は100MBへ変更した。
- すべての取得・更新を所有ユーザーで絞り込み、料理の削除時は手順・履歴・画像パスもごみ箱へ保存して復元できる。
- `E2E-COOKING-001` とDjangoテストを追加。SQLiteの一時検証環境で料理記録テスト18件と `npm run check` は成功した。Dockerデーモン停止中のためPostgreSQLとPlaywright実行は未確認。

## 削除履歴・ごみ箱（2026-07-25）

- `DeletedItem`（migration 0035）へユーザー別の削除スナップショットを保存し、最新10件を超えた古い履歴は自動削除する。
- 対象は家計簿取引、定期支払い、予定、一時タスク／セット、メモ、買いもの、習慣、料理記録。カテゴリ・支払方法などの設定削除は対象外。
- `/carbohydratepro/trash/` から復元でき、元の所有者とIDを保持する。他ユーザーの履歴は一覧・復元ともアクセス不可。
- 習慣の達成記録、繰り返し予定の子予定、一時タスクセット内のカードも親データとまとめて復元する。
- 一括削除と購入済み買いものの削除も履歴へ保存。一時タスクの即時Undoは履歴復元APIを利用する方式へ統一した。
- 検証: Django全492件成功、`npm run check`成功、Playwright全70件成功。新規ユーザーで0%幅になる予算バーの既存E2Eも、外枠と要素の存在を確認する形へ修正した。

機能拡張前のセキュリティ・データ整合性基盤も改善済み（2026-07-12）。

## 基盤改善（2026-07-12）

- 連携アカウントは、新しいセッションで実際に認証したアカウントだけをパスワードなしで切替可能にした。連携関係自体は表示するが、未認証の連携先への切替では再ログインを要求する。
- パスワードリセットメールはユーザー単位で60秒の送信クールダウンを追加（`last_password_reset_email_at`、migration 0006、開発DB適用済み）。
- メール認証再送も60秒のクールダウンを設け、未登録・認証済み・送信対象でメッセージと遷移先が変わらないよう統一した。
- 定期支払い実行を `select_for_update` とトランザクションで冪等化し、同一対象日の重複計上を防止した。
- 習慣、タスク、家計簿、定期支払いの基準日を `timezone.localdate()` / `timezone.localtime()` に統一した。
- Python解析対象を実行環境と同じ3.12へ更新し、READMEから削除済みDRFの記載を除去した。
- 検証: Django全479件成功、`npm run check`成功。ホストにRuff/Pyrightコマンドがないため両ツールは未実行。

## 機能拡張前の新規優先候補

1. 非同期ジョブ＋Outbox基盤（通知、OCR、CSV取込、外部同期の再試行・重複排除）。
2. UserPreference相当のDB永続設定（週開始、テーマ、通知、既定表示の端末間同期）。
3. 関連モデル間のユーザー所有権をサービス層・検証で保証するドメイン境界。
4. 外部連携向けのバージョン付きAPI契約と冪等性キー。

## 直近の改善内容（2026-07-06）

- ログイン一時ロック: 15分間に5回失敗で認証を拒否（`services.is_login_locked`、閾値は `LOGIN_LOCKOUT_THRESHOLD` / `LOGIN_LOCKOUT_WINDOW_MINUTES` で変更可）。
- `get_client_ip` は X-Forwarded-For の右端（信頼プロキシが付加した値）を使用。
- ログイン履歴の地域解決（ipapi.co）はバックグラウンドスレッド化し、ログインをブロックしない。
- DRF（rest_framework / simplejwt）は未使用のため削除。gunicorn イメージ再ビルド済み。
- ログは RotatingFileHandler（10MB×5世代）、django ロガーは INFO に変更。
- アカウント連携は親子リンク方式（`AccountGroupLink`）に変更。追加時は親→子のリンクを作成し、グループ合流はしない。切替候補は「自分＋直接の子」＋「親＋その兄弟」のファミリー範囲。孫や子の別の親は辿らない。子は複数の親に所属可能。旧仕様の同一グループ所属データは解除時に分離される。
- デザイントークン（CSS変数）を `static/app/styles.css` に定義。カードヘッダー・ボタンを統一し、認証系テンプレートのパステル色インラインスタイルを除去。`styles.css` は両 base.html で Bootstrap より後に読み込む。

## 対象リポジトリ

- WSL: `archlinux`
- パス: `/home/carbohydratepro-main`
- ブランチ: `main`
- HEAD: `main`（基盤改善と料理記録は別コミットに分離済み）

## 現在の状態

- プロジェクト本体は `/home/carbohydratepro-main` に存在する。
- ユーザー呼称の `carbohydrate-main` と完全一致するディレクトリは見つからず、実体は `/home/carbohydratepro-main` と判断した。
- 2026-07-12以降の基盤改善と料理記録は、指定どおり別々のコミットに分離した。
- 複数アカウント切替はDB永続の `AccountGroup` / `AccountMembership` と、セッション内の有効アカウント一覧で制御する。
- アカウントアイコンは `CustomUser.avatar` の `FileField` で管理し、JPEG/PNG/WebP、2MB以下に制限する。
- アップロードファイル配信用に `MEDIA_ROOT` / `MEDIA_URL`、Nginx `/media/` alias、Composeの `./media:/var/www/media` を追加した。
- `.gitignore` には既存変更の `workspace/` に加えて `media/` を追加した。
- アカウント追加画面では、新規アカウント作成は一旦提供せず、既存アカウントのログイン追加のみ対応する。
- アカウント切替と解除は `accounts/edit/` のアカウント編集画面に統合し、解除時は確認ダイアログを表示する。
- 現在アカウントをログアウトした場合は、そのアカウントだけをセッション上のログイン済み一覧から外し、残りのログイン済み連携アカウントへ自動切替する。
- ログアウト済みの連携アカウントへ切り替える場合は、対象メールアドレス入力済みのログイン画面へ遷移する。

## UI刷新（2026-07-08）

- アプリシェル: デスクトップは左サイドバー（`app/_sidebar.html`）、モバイルは下部タブ（`app/_bottomnav.html`、その他はドロップアップ）、共通トップバー（`app/_topbar.html`）。ヘッダー帯はユーザー要望で従来のダークカラー（#343a40、`--color-topbar`）を維持。
- デザイントークン: 藍 `--color-primary: #33518e` + 寒色ニュートラル + グレー背景。Bootstrap primary系クラス（.btn-primary等）はstyles.cssでトークンに追従させている。
- ログイン済みの registration 系画面も同じシェル。未ログインページは従来の `registration/_header.html`。旧 `app/_header.html` と挨拶バー（page-greeting）は廃止（E2Eの `login()` はホーム見出しで検証）。
- スケルトンスクリーン: `src/ts/skeleton.ts` が遷移を伴うクリック/フォーム送信で `.skeleton-overlay` を表示。preventDefault済み・外部リンク・アンカーは対象外、bfcache復元で自動解除。
- 注意: PWAのService Workerが有効なブラウザでは Playwright の `page.route` がナビゲーションを捕捉できない。E2Eで遷移を遅延させたい場合は `serviceWorkers: "block"` を使うこと。

## 削除の安全性・一括削除（2026-07-09）

- 共通トースト `src/ts/toast.ts`（全画面で読込、base.html）。`showUndoToast({message,onUndo,onCommit,durationMs})` はタイムアウト/pagehideで onCommit を確定。
- 一時タスク削除は「即削除＋Undoで再作成」（`restoreDeletedTask`）。離脱時の確定は `apiDeleteTask` の `keepalive` に依存。遅延削除方式は離脱レースが残るため不採用。
- 一括削除は共通モジュール `src/ts/bulk_delete.ts` ＋ DOM契約（`data-bulk-container`/`data-bulk-url`、行に `bulk-item`/`data-bulk-id` と `.bulk-check`、`[data-bulk-toggle]`）。メモ・買い物・家計簿に導入。バックエンドは `app/bulk_delete.py` の `bulk_delete_response(request, Model)`。
- デモは `window.DEMO_MODE` を見て実削除せずPOSTだけ投げ、既存インターセプターにブロックさせる。
- task.md「トースト通知の統一」はトースト基盤が入ったので着手しやすい状態（フラッシュメッセージの置換自体は未実施）。

## 予算管理（2026-07-11）

- 新画面 `/carbohydratepro/budget/`（`budget_view`）。`Budget(user, category(null=全体), amount)` モデル、migration 0034。全体予算はユーザー1件（部分ユニーク制約）、カテゴリ別は (user,category) 一意。
- 消化状況は `selectors.build_budget_overview(user, year, month)` が算出（当月Transactionのexpense集計・状況 ok/warning(≥80%)/over(>100%)）。全体予算未設定時はカテゴリ予算合計を目安表示。
- ダッシュボードの収支カードに予算バーを統合（`home_views` が budget_overall/budget_over_count を渡す）。家計簿ページに「予算」ボタン。
- デモは `get_budget_context`/`demo_budget`/`/demo/budget/`、settingsRedirectMap に `/carbohydratepro/budget/`→`/demo/budget/`。フォームPOSTは既存インターセプターがブロック。
- 次の新機能候補（未着手）: 統合カレンダー、週次レビュー＋通知、気分・ジャーナル、目標トラッカー、サブスク管理、クイック入力。

## 外部カレンダー取り込み（2026-07-09）

- ICS購読: `ExternalCalendar`（URL登録）→ cron（30分ごと、`sync_external_calendars`）で `ExternalEvent` に洗い替え。RRULEは recurring-ical-events で展開。依存に icalendar / recurring-ical-events を追加（イメージ再ビルド必要、migration 0033）。
- SSRF対策: `services._assert_public_host`（is_global チェック）+ リダイレクトごと再検証 + 5MB上限。webcal:// は https:// に正規化。
- 表示: ExternalEvent は Task 互換プロパティ（is_external/label=calendar）を持ち、月カレンダー・ガント・日別JSON・ダッシュボードにマージ。テンプレートは `task.is_external` で編集リンクを外す。

## 新機能（2026-07-07）

- 統合ダッシュボード `/carbohydratepro/home/`（ログイン後の遷移先。今日のタスク・習慣・今月の収支・買い物・メモを集約。デモは `/demo/home/`）。
- ICSカレンダー配信 `/calendar/<token>.ics`（`CalendarToken` モデル、タスク設定画面でURL表示・コピー・再生成）。
- PWA対応（`manifest.webmanifest`、`/sw.js` はルートスコープ配信のため `templates/sw.js`、オフライン時は `/offline/`）。

## デプロイ状況（2026-07-08）

- コミット 0269de8 までを本番（54.238.169.177）へデプロイ済み（外部カレンダー取り込み・Undoトースト・選択モード一括削除まで含む）。マイグレーションは0033まで適用。icalendar/recurring-ical-events追加のためイメージ再ビルド実施。cronに外部カレンダー同期（30分毎）が入っていることを確認。メンテナンスモード有効→解除の手順で実施（2026-07-09）。
- デプロイ直後にルートURLが500になる障害が発生。原因は AdminSecurityMiddleware が名前なしURLパターン（url_name=None）で `'admin' in None` の TypeError を起こすこと（ADMIN_ENABLED=False の本番のみ発火、devでは再現しない）。None を空文字扱いに修正しホットフィックス済み（3e627cd）。
- AdminSecurityMiddleware の握りつぶされていた `raise Http404` を修正し管理ブロックを有効化（secure_admin は除外）。旧 /admin/ が Http404 を return していて500になる問題も修正（780be2d、ユーザー承認済み・本番反映済み）。
- Playwright E2E はスイート全60件成功。WSL(Arch)に pacman でChromium実行用ライブラリを導入済み。

## 次に行うこと

1. Docker起動後にmigration 0037をPostgreSQLで適用し、関連Djangoテストを実行する。
2. 認証済み環境で `E2E-FIXES-001` と `E2E-COOKING-001` を実行する。
3. migration 0035・0036・0037を含む本番リリース時期を決める。

## 作業上の注意

- 変更後は `activeContext.md` と `progress.md` を更新する。
- TypeScript変更では `src/ts/` を編集し、`static/app/` はビルド出力として扱う。
- DockerやWSLコマンドは必要に応じて `wsl.exe -d archlinux -- ...` 経由で実行する。
- Gitコミットメッセージは必ず日本語にする。
