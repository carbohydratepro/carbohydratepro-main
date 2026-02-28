# CLAUDE.md

## JavaScript / TypeScript のコーディング規約

- フロントエンドのスクリプトは **TypeScript** で記述すること（`src/ts/` 以下）
- `var` は使用しないこと。`const` または `let` を使用する
- 極力 Vanilla JS を使用し、jQuery の使用は避けること
- `any` 型の使用は避けること。`unknown` を使用して適切に型を絞り込む
- 関数の引数と戻り値には必ず型アノテーションを付けること
- TypeScript のコンパイルは `npm run build`（または `npm run watch`）で実行すること
- コンパイル済み JS（`static/app/*.js`）は直接編集せず、`src/ts/*.ts` を編集してビルドすること
