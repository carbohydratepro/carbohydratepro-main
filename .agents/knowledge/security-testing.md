---
name: security-testing
description: ZAPなどの動的セキュリティスキャンを実行・事故復旧するとき
scope: project
updated: 2026-09-01
---

# 動的セキュリティスキャン

本番環境にOWASP ZAPをかける場合は、既定で攻撃を行わないBaseline Scanだけを使う。
Full ScanやActive Scanは、原則としてローカルまたはステージングで実施する。

- 本番Baseline Scanは公式安定版 `ghcr.io/zaproxy/zaproxy:stable` を使う。
- 公開範囲の開始点は `https://carbohydratepro.com/demo/expenses/` とする。
- 本番でFull ScanやActive Scanが必要な場合は、対象・負荷・実施時間を明示し、別途承認を得る。
- 未認証Baseline Scanでは認証後画面を評価できない。認証スキャンにはZAP contextを用意し、認証情報をリポジトリやレポートへ残さない。
- 標準の全画面確認では、匿名・通常ユーザー・管理権限の3範囲を分けて対象にする。認証後画面はローカルの専用一時アカウントでスキャンし、実ユーザーや本番データを使わず、終了時にアカウントとセッションを削除する。
- **認証済み画面、とくにDjango管理サイトへZAP Spiderを使わない。** Baseline/受動スキャンでもTraditional SpiderはHTMLフォームを自動POSTし、追加・更新・削除を成立させる。全画面確認はGETだけの明示URL許可リスト（Automation Frameworkのrequestor等）で行うか、終了後に破棄・復元できる隔離DBを使う。
- 生成レポートは `workspace/zap/YYYY-MM-DD/` に置く。`workspace/` はgit管理外であり、スキャン結果を不用意にコミットしない。

本番でBaseline Scanを選ぶ理由は、能動攻撃を避けて公開面の初期評価ができるため。ただし「能動攻撃なし」は「GETのみ・データ変更なし」を意味しない。フォームを含む認証済み範囲ではSpiderを除外する。Full Scanは能動的な攻撃を含み、サービス負荷やデータ変更の可能性があるため棄却する。

## 誤更新・削除が起きた場合

- 対象DBを使うWeb・バッチサービスを停止し、元のDBボリュームを再起動・VACUUMしない。まず論理dump、監査ログ、停止状態の物理ボリュームを別々に退避してハッシュを残す。
- 論理dumpにはMVCC上の不可視タプルが含まれない。物理コピーを別ボリュームへ展開し、`autovacuum=off`・外部ポート非公開で調査する。元ボリュームへ解析ツールを接続しない。
- PostgreSQLの`archive_mode=off`では通常のPITRはできない。ただし保持WALのフルページイメージがあれば、`pg_waldump --save-fullpage`と`pageinspect`で、剪定済みの行もページ単位で復号できる場合がある。
- 最初の破壊操作を含むフルページイメージには削除対象のタプル本体が残る。復号はさらに別の使い捨てDBで行い、元の型システムから復旧データを生成する。
- 復旧手順は未加工スナップショットの複製へ先に適用し、件数検査、Django `check`、復号元との全行・全カラムハッシュ一致を確認する。元DBへの適用は別途承認を得る。
- Djangoの`on_delete=models.CASCADE`はDB制約の`ON DELETE CASCADE`とは限らない。一時ユーザーの削除は生SQLではなくDjango ORMで行い、関連オブジェクトをCollectorに処理させる。
