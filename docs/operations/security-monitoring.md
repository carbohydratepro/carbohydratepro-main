# セキュリティ監視・通知

## 通知の振り分け

- 2分ごとにログを収集し、速報対象を1通へまとめる。同じ種類の再通知は60分間抑制する。
- 速報対象: 明示的なCRITICAL、5分間に10件以上のアプリERROR、許可範囲外のSSHログイン、SSH認証失敗の集中（5分20件）、監視対象ファイル変更、アップロード領域の実行形式ファイル、新しい待受ポート、ホスト監視の停止・失敗。
- 単発ERROR、拒否済みアクセス、通常の特権ログイン、予定メンテナンスは毎朝6時（JST）の日次レポートへ集約する。
- 初回取り込み時の過去ログは速報せず、直近5分だけ対象にする。初回以降の未通知CRITICALは収集の再開後にも通知対象とする。
- 日次は成功1回/日。失敗時は手動または次回の実行で再試行可能。速報はメール送信が成功しなければ次の2分周期で再試行する。
- メールとイベントDBには分類・時刻・件数だけを残し、ログ本文、メールアドレス、IP、トークン、ファイル内容を転記しない。
- メール受け付け直後のプロセス停止・DB障害では重複が起こり得る。配送時間も含めた厳密な到着保証はない。

アプリの予定されたメンテナンス応答だけをINFOに分類する。通常の503や障害はERRORのまま。
`SEND_INSTANT_SECURITY_EMAIL` は従来の特権ログイン直送であり、今回の速報とは別物。通知をまとめる運用ではFalseを維持する。

## 管理パネル

スーパーユーザーのみ、管理パネルで30日間の日別グラフ・件数表・直近20件の分類を確認できる。
日付はJSTの暦日。日次メールの前日6時〜当日6時とは集計境界が異なる。
未収集期間は未収集と表示し、5分以上集計が更新されなければ警告する。記録は90日保持する。
ログのローテーションを含む再読み込みはfingerprintで重複を抑止する。同一ミリ秒の同一内容も行数を保持する。
ログが消去・改ざんされた場合や長期間停止して保存世代を超えた場合、完全な件数復元は保証しない。

## 検出範囲と限界

| 対象 | 対応 | 限界 |
|---|---|---|
| Web管理画面探索・CSRF拒否 | 既存アプリログから集計、日次 | 拒否ログは侵入成功の証拠ではない |
| アプリ障害 | CRITICALとERROR急増は速報、単発ERRORは日次 | DB・cron・ホスト全体が停止するとこの仕組みも停止 |
| SSHログイン・認証失敗 | ホストcollectorでjournaldを収集。許可ユーザーと接続元範囲で分類 | 信頼範囲内からの盗難鍵利用は検出できない。成功ログだけで本人性は証明できない |
| ファイル追加・変更・削除、権限変更 | 明示した監視パスをレビュー済みbaselineと比較 | 全ディスクではない。正常なデプロイも変更になる |
| 不審ファイル | upload_rootsで実行系拡張子、ELF/PE/shebang/PHP先頭、symlinkを検出 | すべてのマルウェア・偽装形式・メモリ上の侵害は検出できない |
| 待受ポートの追加 | ホストのTCP/UDP待受をbaselineと比較 | ホストから見えないコンテナ内部の待受や一時的な短時間の待受は対象外 |
| 外部からのポートスキャン | **未対応** | 接続試行/拒否のパケットログを別途収集する必要がある。Lightsail側で遮断された通信はホストに届かない |
| ホスト監視の停止 | アプリがheartbeatを確認し、5分超の遅延・失敗を速報 | アプリ側も同時停止した場合に備え、別ホストからの外形監視が必要 |

root権限を奪われるとホスト内の監視や証拠も改ざん可能。既存の外部ログ保存を維持し、独立した外形監視を併用する。
この仕組みを「侵入がないことの証明」やEDR/IDSの代替として扱わない。

## 本番へ適用するとき

1. 対象ソースとDBバックアップを確認し、auth_appの新しいmigrationを適用する。
2. `/etc/carbohydratepro/host-monitor.json` をroot所有0600で準備する。次の例の値は**環境に合わせてレビュー**する。

```json
{
  "state_dir": "/var/lib/carbohydratepro-monitor",
  "watch_paths": ["/etc/ssh", "/etc/crontab", "/etc/cron.d", "/etc/systemd/system", "/usr/local/libexec/carbohydratepro", "/home/APP_USER/.ssh/authorized_keys"],
  "upload_roots": ["/home/APP_USER/APP_REPOSITORY/media"],
  "ssh_users": ["APP_USER"],
  "ssh_networks": ["192.0.2.10/32"]
}
```

3. 異常がないことを確認したホストで `sudo bash scripts/install-host-security-monitor.sh` を実行する。初回だけbaselineを作成する。既存baselineは上書きしない。root collectorはアプリの書き換え可能な領域から直接実行せず、root所有のコピーを使う。
4. Compose用 `.env` に `SECURITY_MONITOR_EXPORT_DIR=/var/lib/carbohydratepro-monitor/export` を設定。`secret.env` に `SECURITY_HOST_MONITOR_ENABLED=True`、`SEND_URGENT_SECURITY_EMAIL=True` を設定する。
5. cronイメージを再ビルドし、cron/gunicornコンテナを再作成して新しいcrontab・設定・読み取り専用exportマウントを反映する。単なるrestartでは設定は変わらない。必要な静的ファイルをcollectstaticする。
6. 新しい監視データの取り込みは **cronコンテナ** で実行する。gunicornにはホストexportをマウントしない。`check_security_log --urgent` は有効化後に実メールを送る可能性があるため、テスト送信を意図せず本番検証として実行しない。
7. 管理画面の最終集計・サーバー監視状態、systemd timer、SMTP配送を確認する。

ホスト2分周期＋アプリ2分周期により、正常稼働時は通常1〜5分程度で通知処理へ進む。メール配送遅延や同種の60分抑制は別扱い。

baseline変更を自動承認しない。正常な運用変更であることを差分・権限・出所で確認し、旧baselineをroot専用領域へ退避してから明示的に再初期化する。
不審なファイルは自動実行・削除しない。対象の詳細はroot専用の `/var/lib/carbohydratepro-monitor/details.jsonl` に残る。
SSHのjournal cursorが失効した場合は失敗として通知する。保全したログを確認し、復旧の収集開始点を判断してからcursorを更新する。

ホスト監視の参考: [systemd journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)、[Lightsailファイアウォール](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-firewall-and-port-mappings-in-amazon-lightsail.html)。

## 運用確認

運用全体・S3退避は[本番運用・容量管理](production-maintenance.md)を参照。
`security.log`（WARNING以上）と`django_debug.log`（INFO以上）は10MB×5世代でローテーションし、現在ログと世代ログを収集する。既存の毎時S3退避も維持する。
`check_debug_log`の旧5分メールは再登録しない。`SECURITY_REPORT_MAX_DETAILS`は互換用設定として残るが、この日次レポートでは使用しない。

| 設定 | 既定値 | 用途 |
|---|---|---|
| `SEND_PERIODIC_SECURITY_EMAIL` | True | 毎朝6時の日次メール |
| `SEND_URGENT_SECURITY_EMAIL` | False | 2分周期の重要メール。導入確認後に有効化 |
| `SEND_INSTANT_SECURITY_EMAIL` | False | 旧特権ログイン直送。Falseを維持 |
| `SECURITY_HOST_MONITOR_ENABLED` | False | ホストexportの取り込み |
| `SECURITY_ALERT_EMAIL` | アプリ既定値 | 通知先 |

SMTP認証情報は`secret.env`に置き、Git・ログ・文書へ転記しない。

```bash
docker compose -f docker-compose-dev.yml ps cron
docker exec cron cat /etc/cron.d/recurring-payments
docker logs cron --tail 100
systemctl list-timers carbohydratepro-security-monitor.timer
```

`/var/log/cron.log`はコンテナ標準出力へ転送される。メール過多なら、ホストcronの重複登録・旧`check_debug_log`・旧特権ログイン直送の有効化を確認する。未着なら最終集計時刻、監視停止表示、SMTP失敗、各送信フラグを確認する。日次の送信履歴は`SecurityReportDelivery`、速報は`SecurityAlertState`に残る。

検証はDjangoのlocmemメールバックエンドと合成ログを使い、実メールの試験送信や不審ファイルの実行は行わない。
