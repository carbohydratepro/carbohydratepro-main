// 固定済みnpm依存から配信用ファイルを作る。アプリコードはsrc/tsで管理する。
import { mkdir, readFile, writeFile, copyFile } from 'node:fs/promises';

const destination = new URL('../static/app/vendor/', import.meta.url);
await mkdir(destination, { recursive: true });
const source = await readFile(new URL('../node_modules/chart.js/dist/chart.umd.js', import.meta.url), 'utf8');
await writeFile(new URL('chart.umd.js', destination), source.replace(/\/\/# sourceMappingURL=.*$/gm, '').trimEnd() + '\n');
await copyFile(new URL('../node_modules/chart.js/LICENSE.md', import.meta.url), new URL('chart-LICENSE.md', destination));
