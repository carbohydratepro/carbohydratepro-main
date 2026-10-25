import { expect, test } from '../fixtures/base';
import { expectNoHorizontalOverflow } from '../fixtures/http';
import * as path from 'node:path';

for (const width of [390, 1440]) {
  test(`E2E-MOTION-001 ${width}pxで動きのCSSが静止時の外観を変えない`, async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#interaction-motion
    await page.setViewportSize({ width, height: 900 });
    for (const route of ['/demo/home/', '/demo/expenses/', '/demo/board/', '/demo/memos/', '/login/']) {
      await page.goto(route);
      const link = page.locator('link[href*="interaction-motion"]');
      await expect(link).toHaveCount(1);
      await expect(page.locator('link[href*="workspace.css"], link[href*="lucian-shell.css"]')).toHaveCount(0);
      const snapshot = () => page.locator('.app-topbar, .app-sidebar, .app-main, .card, .btn, .board-status-switch').evaluateAll(elements => elements.map(el => {
        const style = getComputedStyle(el), box = el.getBoundingClientRect();
        return { x: box.x, y: box.y, w: box.width, h: box.height, color: style.color, background: style.backgroundColor, radius: style.borderRadius, font: style.fontSize };
      }));
      const withMotion = await snapshot();
      await link.evaluate(el => { (el as HTMLLinkElement).disabled = true; });
      expect(await snapshot()).toEqual(withMotion);
      await link.evaluate(el => { (el as HTMLLinkElement).disabled = false; });
      await expectNoHorizontalOverflow(page);
    }
  });
}

test('E2E-MOTION-002 押下の反応と動きを減らす設定を維持する', async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#interaction-motion
  await page.setContent('<button class="btn">保存</button><button class="btn" disabled>無効</button><div class="dropdown-menu show">操作</div><div class="modal fade"><div class="modal-dialog">入力</div></div>');
  await page.addStyleTag({ path: path.resolve('static/app/interaction-motion.css') });
  const save = page.getByRole('button', { name: '保存' });
  await save.hover();
  await page.mouse.down();
  await expect(save).toHaveCSS('translate', '0px 1px');
  await page.mouse.up();
  await expect(save).toHaveCSS('translate', 'none');
  await expect(page.locator('.modal-dialog')).toHaveCSS('transition-duration', '0.16s');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await save.hover();
  await page.mouse.down();
  await expect(save).toHaveCSS('translate', 'none');
  await page.mouse.up();
  await expect(page.locator('.modal-dialog')).toHaveCSS('transform', 'none');
  await expect(page.locator('.modal-dialog')).toHaveCSS('transition-duration', '0s');
  await expect(page.locator('.dropdown-menu')).toHaveCSS('animation-name', 'none');
});
