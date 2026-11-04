import { expect, test } from '../fixtures/base';
import { login } from '../fixtures/auth';

// 専用の管理者テストアカウントを使う。本番アカウントでは実行しない。
test('E2E-SECURITY-001 管理者が検出グラフと件数表をPC・モバイルで確認できる', async ({ page }) => {
  const email = process.env.E2E_ADMIN_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD;
  test.skip(!email || !password, '専用の E2E_ADMIN_EMAIL/E2E_ADMIN_PASSWORD が必要です');
  await login(page, { email: email!, password: password! });
  await page.goto('/carbohydratepro/manage/');
  const panel = page.getByRole('region', { name: 'セキュリティ・エラー検出' });
  await expect(panel).toBeVisible();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(panel.getByRole('img')).toBeVisible();
    await expect.poll(() => panel.getByRole('img').evaluate((canvas: HTMLCanvasElement) => {
      const pixels = canvas.getContext('2d')?.getImageData(0, 0, canvas.width, canvas.height).data;
      return pixels?.some((value, index) => index % 4 === 3 && value > 0) ?? false;
    })).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await panel.getByText('日別の件数を表で表示', { exact: true }).click();
  await expect(panel.getByRole('table')).toBeVisible();
  await expect(panel.getByRole('row')).toHaveCount(31);
  await expect(panel.getByRole('columnheader', { name: 'エラー', exact: true })).toBeVisible();
});
