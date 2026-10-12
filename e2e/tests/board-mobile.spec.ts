import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { uniqueName, expectNoHorizontalOverflow } from "../fixtures/http";

test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
test.beforeEach(async ({ page }) => {
  await login(page, getCredentialsOrSkip());
  await page.goto('/carbohydratepro/tasks/board/');
  await expect(page.locator('#input-todo')).toBeEnabled();
});

test('E2E-BOARD-UI-001 タップで追加・編集・移動・完了・削除・復元できる', async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#board-mobile
  const title = uniqueName('スマホタスク');
  await page.locator('#input-todo').fill(title);
  await page.locator('#col-todo .kanban-add-btn').tap();
  const task = page.getByRole('button', { name: title, exact: true });
  await expect(task).toBeEnabled();
  await task.tap();
  const sheet = page.getByRole('dialog', { name: 'タスクを編集' });
  await expect(sheet).toBeVisible();
  await page.screenshot({ path: '/tmp/board-sheet-after.png' });
  await sheet.getByLabel('状態', { exact: true }).selectOption('doing');
  await sheet.getByRole('button', { name: '保存', exact: true }).tap();
  await expect(sheet).toBeHidden();
  await page.getByRole('button', { name: /^進行中 \d/ }).tap();
  await page.locator('.kanban-task-card').filter({ has: task }).getByRole('button', { name: '完了にする' }).tap();
  await page.getByRole('button', { name: /^完了 \d/ }).tap();
  await expect(task).toBeEnabled();
  await task.tap();
  await sheet.getByRole('button', { name: '削除', exact: true }).tap();
  await expect(task).toHaveCount(0);
  await page.getByRole('button', { name: '元に戻す', exact: true }).tap();
  await expect(task).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: /^完了 \d/ }).tap();
  await expect(task).toBeVisible();
  await page.screenshot({ path: '/tmp/board-mobile-after.png', fullPage: true });
});

test('E2E-BOARD-UI-002 編集失敗でも入力を保持し再保存できる', async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#board-mobile
  const title = uniqueName('保存テスト');
  await page.locator('#input-todo').fill(title);
  await page.locator('#col-todo .kanban-add-btn').tap();
  const task = page.getByRole('button', { name: title, exact: true });
  await expect(task).toBeEnabled();
  await task.tap();
  const sheet = page.getByRole('dialog', { name: 'タスクを編集' });
  await sheet.getByLabel('タスク名', { exact: true }).fill(title + '変更');
  await page.route('**/tasks/board/api/*/', async route => {
    if (route.request().method() === 'PUT') await route.fulfill({ status: 200, contentType: 'application/json', body: '{' });
    else await route.continue();
  });
  await sheet.getByRole('button', { name: '保存', exact: true }).tap();
  await expect(sheet.getByRole('alert')).toContainText('入力は保持');
  await expect(sheet.getByLabel('タスク名', { exact: true })).toHaveValue(title + '変更');
  await page.unroute('**/tasks/board/api/*/');
  await sheet.getByRole('button', { name: '保存', exact: true }).tap();
  await expect(sheet).toBeHidden();
  await expect(page.getByRole('button', { name: title + '変更', exact: true })).toBeVisible();
});

test('E2E-BOARD-UI-003 スマホ幅で1列・タッチ領域・非ドラッグ操作を維持する', async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#board-mobile
  const title = uniqueName('操作対象');
  await page.locator('#input-todo').fill(title);
  await page.locator('#col-todo .kanban-add-btn').tap();
  const task = page.getByRole('button', { name: title, exact: true });
  await expect(task).toBeEnabled();
  for (const width of [320, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(page.locator('.kanban-column:visible')).toHaveCount(1);
    await expectNoHorizontalOverflow(page);
    expect((await task.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    const card = page.locator('.kanban-task-card').filter({ has: task });
    await expect(card).toHaveCSS('touch-action', 'pan-y pinch-zoom');
    expect(await card.evaluate(el => {
      const touch = new Touch({ identifier: 1, target: el, clientX: 150, clientY: 400 });
      return el.dispatchEvent(new TouchEvent('touchstart', { touches: [touch], bubbles: true, cancelable: true }));
    })).toBe(true);
    await expect(page.locator('#dragOverlay')).toHaveCount(0);
  }
});

test('E2E-BOARD-UI-004 セット追加と名前変更をパネル内で操作する', async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#board-mobile
  const name = uniqueName('集中リスト');
  await page.getByRole('button', { name: 'セットを追加', exact: true }).tap();
  const sheet = page.locator('#boardSetSheet');
  await sheet.getByLabel('セット名', { exact: true }).fill(name);
  await sheet.getByRole('button', { name: '保存', exact: true }).tap();
  await expect(sheet).toBeHidden();
  await expect(page.getByRole('button', { name, exact: true })).toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', { name: '一時タスクのその他の操作' }).tap();
  await page.getByRole('button', { name: 'セット名を変更', exact: true }).tap();
  await sheet.getByLabel('セット名', { exact: true }).fill(name + '改');
  await sheet.getByRole('button', { name: '保存', exact: true }).tap();
  await expect(page.getByRole('button', { name: name + '改', exact: true })).toBeVisible();
});

test.describe('デスクトップとデモ', () => {
  test.use({ viewport: { width: 1440, height: 900 }, hasTouch: false, isMobile: false });
  test('E2E-BOARD-UI-005 PCの3列・キーボード編集とデモを維持する', async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#board-mobile
    const title = uniqueName('キーボード');
    await page.locator('#input-todo').fill(title);
    await page.locator('#input-todo').press('Enter');
    const task = page.getByRole('button', { name: title, exact: true });
    await expect(task).toBeEnabled();
    await expect(page.locator('.kanban-column:visible')).toHaveCount(3);
    await task.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog', { name: 'タスクを編集' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(task).toBeFocused();
    await page.screenshot({ path: '/tmp/board-desktop-after.png', fullPage: true });
    await page.goto('/demo/board/');
    await expect(page.locator('.kanban-task-card').first()).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator('.kanban-column:visible')).toHaveCount(1);
    await expectNoHorizontalOverflow(page);
  });
});
