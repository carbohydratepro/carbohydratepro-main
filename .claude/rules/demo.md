## デモモードのルール

デモモードはログイン不要でアプリの全機能を閲覧できる仕組みで、以下のファイルで構成されている。

- `auth_app/demo_data.py` — フェイクデータクラスとコンテキスト生成関数
- `auth_app/demo_views.py` — デモ用ビュー関数
- `auth_app/urls.py` — `/demo/...` URLパターン
- `app/templates/app/base.html` — デモバナー、デモモーダル、fetch/フォームインターセプター、`settingsRedirectMap`

### 新しい画面・機能を追加した場合の対応

1. **`demo_data.py`** にフェイクデータクラスとコンテキスト生成関数を追加する
2. **`demo_views.py`** にデモ用ビュー関数を追加する（`is_demo=True` をコンテキストに含める）
3. **`auth_app/urls.py`** に `/demo/<path>/` URLパターンを追加する
4. **`base.html`** の `settingsRedirectMap` に実URLからデモURLへのマッピングを追加する
   - ヘッダー等からリンクされているページは必ずマッピングを追加すること
5. デモモードでブロックすべき新しい操作（fetch API、フォーム送信等）がある場合は、
   `base.html` のインターセプターにパターンを追加すること

### 基本方針

- デモでは閲覧のみ許可し、登録・更新・削除は `#demoSignupModal` を表示してブロックする
- フェイクデータは実際の画面と見分けがつかない程度にリアルなデータを使用する
