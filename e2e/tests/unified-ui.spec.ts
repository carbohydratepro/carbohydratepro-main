import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { expectNoHorizontalOverflow } from "../fixtures/http";

test("E2E-UI-014 認証・補助画面にも共通部品が適用される", async ({ page }, testInfo) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-014
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const path of ["/top/", "/login/", "/signup/", "/password_reset/", "/password_reset_done/", "/password_reset_complete/", "/signup_done/", "/resend-verification/"]) {
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);
      await expect(page.locator('head link[href*="/app/ui-components."]')).toHaveCount(1);
      await expectNoHorizontalOverflow(page);
    }
  }
  await login(page, getCredentialsOrSkip());
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const path of ["/accounts/select/", "/accounts/add/", "/accounts/edit/", "/password_change/", "/carbohydratepro/trash/", "/carbohydratepro/budget/", "/carbohydratepro/contact/", "/carbohydratepro/habits/list/"]) {
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);
      await expect(page.locator('head link[href*="/app/ui-components."]')).toHaveCount(1);
      await expectNoHorizontalOverflow(page);
      if (width === 390) {
        await page.screenshot({ path: testInfo.outputPath(`${path.replaceAll("/", "-")}.png`), fullPage: true });
      }
    }
  }
});

test("E2E-UI-015 確認ダイアログはフォーカスを維持して呼出元へ戻す", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-015
  await page.goto("/demo/shopping/");
  const trigger = page.getByRole("button", { name: "検索", exact: true });
  await trigger.focus();
  await page.evaluate(() => {
    const api = window as unknown as { showConfirm: (options: { message: string; onConfirm: () => void }) => void };
    api.showConfirm({ message: "確認のテスト", onConfirm: () => {} });
  });
  const dialog = page.getByRole("alertdialog", { name: "確認のテスト" });
  const cancel = dialog.getByRole("button", { name: "キャンセル" });
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(dialog.getByRole("button", { name: "OK", exact: true })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
});
