# CLAUDE.md

## ルール

### ロックファイルの取り扱い

- ロックファイル（`package-lock.json`, `poetry.lock`, `Pipfile.lock` 等）は直接編集しないこと
- 依存関係の更新はパッケージマネージャーのコマンド（`npm install`, `poetry lock`, `pip freeze` 等）を通して行うこと

### JavaScript のコーディング規約

- `var` は使用しないこと。`const` または `let` を使用する
- 極力 Vanilla JS を使用し、jQuery の使用は避けること
