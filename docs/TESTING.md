# テスト実施ガイド

このドキュメントでは、CarbohydrateProプロジェクトのテスト実施方法について説明します。

## テスト構成

テストは以下のディレクトリに配置されています：

```
app/
  tests/
    __init__.py
    test_expenses.py    # 支出管理機能のテスト
    test_task.py        # タスク管理機能のテスト
    test_memo.py        # メモ機能のテスト
    test_shopping.py    # 買い物リスト機能のテスト
    test_filters.py     # テンプレートフィルターのテスト

auth_app/
  tests/
    __init__.py
    test_auth.py        # 認証機能のテスト

project/
  tests/
    __init__.py
    test_utils.py       # ユーティリティ関数のテスト
```

## テストの実行

### Docker環境でのテスト実行

開発環境ではDocker Composeを使用してテストを実行します。

#### 全テストの実行

```bash
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test
```

#### 特定アプリのテスト実行

```bash
# 支出管理のテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_expenses

# タスク管理のテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_task

# メモ機能のテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_memo

# 買い物リストのテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_shopping

# テンプレートフィルターのテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_filters

# 認証機能のテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test auth_app.tests.test_auth

# ユーティリティのテスト
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test project.tests.test_utils
```

#### 特定テストクラスの実行

```bash
# 例: TransactionModelTestクラスのみ実行
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_expenses.TransactionModelTest
```

#### 特定テストメソッドの実行

```bash
# 例: test_create_expense_transactionメソッドのみ実行
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test app.tests.test_expenses.TransactionModelTest.test_create_expense_transaction
```

### テストオプション

#### 詳細出力

```bash
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test -v 2
```

#### 失敗したテストで停止

```bash
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test --failfast
```

#### カバレッジ測定（coverageインストール時）

```bash
docker-compose -f docker-compose-dev.yml exec gunicorn coverage run manage.py test
docker-compose -f docker-compose-dev.yml exec gunicorn coverage report
```

## テストカテゴリ

### モデルテスト

各モデルの基本的な動作を検証します：
- モデルの作成
- フィールドの制約
- `__str__`メソッド
- 自動計算フィールド
- 並び順（ordering）

### フォームテスト

フォームのバリデーションを検証します：
- 有効なデータでのバリデーション成功
- 必須フィールドの検証
- カスタムバリデーション
- ユーザー固有のクエリセットフィルタリング

### ビューテスト

ビューの動作を検証します：
- ログイン要求
- GETリクエストでのページ表示
- POSTリクエストでのデータ作成・更新・削除
- 権限チェック（他ユーザーのデータへのアクセス禁止）
- 検索・フィルタリング機能
- ページネーション
- AJAX対応

## テスト作成ガイドライン

### 命名規則

- テストクラス名: `<機能名>Test`（例: `TransactionModelTest`）
- テストメソッド名: `test_<動作の説明>`（例: `test_create_expense_transaction`）

### テストの構造

```python
def test_<動作の説明>(self) -> None:
    """日本語でのテスト説明"""
    # Arrange: テストデータの準備
    # Act: テスト対象の操作実行
    # Assert: 結果の検証
```

### 共通のセットアップ

各テストクラスの`setUp`メソッドで共通のテストデータを作成します：

```python
def setUp(self) -> None:
    User = get_user_model()
    self.user = User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123',
        is_email_verified=True,
    )
    self.client.login(username='test@example.com', password='testpass123')
```

### モックの使用

外部サービス（メール送信など）はモックを使用します：

```python
from unittest.mock import patch

@patch('auth_app.views.send_html_email', return_value=True)
def test_signup_success(self, mock_send_email) -> None:
    # テストコード
    mock_send_email.assert_called_once()
```

## テストカバレッジ

現在のテストカバレッジ対象：

### 支出管理（expenses）
- [x] PaymentMethodモデル
- [x] Categoryモデル
- [x] Transactionモデル
- [x] TransactionForm
- [x] PaymentMethodForm
- [x] CategoryForm
- [x] 支出一覧ビュー
- [x] 支出作成ビュー
- [x] 支出編集ビュー
- [x] 支出削除ビュー
- [x] 支出設定ビュー
- [x] 検索・フィルタリング
- [x] ページネーション
- [x] AJAX対応

### タスク管理（task）
- [x] TaskLabelモデル
- [x] Taskモデル
- [x] TaskForm
- [x] TaskLabelForm
- [x] タスク一覧ビュー
- [x] タスク作成ビュー
- [x] タスク編集ビュー
- [x] タスク削除ビュー
- [x] タスク設定ビュー
- [x] 繰り返しタスク

### メモ（memo）
- [x] MemoTypeモデル
- [x] Memoモデル
- [x] MemoForm
- [x] MemoTypeForm
- [x] メモ一覧ビュー
- [x] メモ作成ビュー
- [x] メモ編集ビュー
- [x] メモ削除ビュー
- [x] お気に入り切り替え
- [x] メモ設定ビュー

### 買い物リスト（shopping）
- [x] ShoppingItemモデル
- [x] ShoppingItemForm
- [x] 買い物リスト一覧ビュー
- [x] アイテム作成ビュー
- [x] アイテム編集ビュー
- [x] アイテム削除ビュー
- [x] 残数更新ビュー
- [x] ステータス自動更新

### 認証（auth）
- [x] CustomUserモデル
- [x] EmailVerificationTokenモデル
- [x] LoginHistoryモデル
- [x] ログインビュー
- [x] サインアップビュー
- [x] メール認証ビュー
- [x] 認証メール再送信ビュー
- [x] パスワードリセットビュー
- [x] パスワード変更ビュー
- [x] マイページビュー

### ユーティリティ
- [x] strip_html_tags関数
- [x] send_html_email関数
- [x] CHART_COLORS定数
- [x] MAJOR_CATEGORY_LABELS定数

### テンプレートフィルター
- [x] highlightフィルター（XSS対策含む）
- [x] comma_formatフィルター
- [x] darkerフィルター

## トラブルシューティング

### テストデータベースの問題

テストデータベースの作成に問題がある場合：

```bash
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py migrate --run-syncdb
```

### テストが見つからない場合

`__init__.py`ファイルがテストディレクトリに存在することを確認してください。

### モジュールインポートエラー

Dockerコンテナを再起動してください：

```bash
docker-compose -f docker-compose-dev.yml down
docker-compose -f docker-compose-dev.yml up -d
```
