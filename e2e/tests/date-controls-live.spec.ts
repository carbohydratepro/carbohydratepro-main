import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { expectNoHorizontalOverflow } from "../fixtures/http";

test("E2E-UI-018 取引フォームの日付欄を他の入力欄に揃える", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-018
  await login(page, getCredentialsOrSkip());
  await page.goto("/carbohydratepro/expenses/");
  await page.getByRole("button", { name: /収支登録/ }).click();
  const modal = page.locator("#createModal");
  await expect(modal.getByRole("heading", { name: "取引新規登録" })).toBeVisible();
  for (const forceIOSStyles of [false, true]) {
    if (forceIOSStyles) {
      // ChromiumでiOS向けCSSの寸法だけを検証する。iOSネイティブ描画の検証ではない。
      const css = await page.evaluate(() => Array.from(document.styleSheets)
        .filter((sheet) => sheet.href?.includes("ui-components"))
        .flatMap((sheet) => Array.from(sheet.cssRules))
        .filter((rule): rule is CSSSupportsRule => rule instanceof CSSSupportsRule
          && rule.conditionText.includes("-webkit-touch-callout"))
        .flatMap((rule) => Array.from(rule.cssRules).map((child) => child.cssText))
        .join("\n"));
      expect(css).not.toBe("");
      await page.addStyleTag({ content: css });
    }
    for (const width of [320, 390, 430, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      const date = modal.getByLabel("日付", { exact: true });
      for (const value of ["", "2026-09-27"]) {
        await date.fill(value);
        const bounds = (await date.boundingBox())!;
        for (const label of ["金額", "用途"]) {
          const other = (await modal.getByLabel(label, { exact: true }).boundingBox())!;
          expect(Math.abs(bounds.x - other.x)).toBeLessThan(1);
          expect(Math.abs(bounds.width - other.width)).toBeLessThan(1);
          expect(Math.abs(bounds.height - other.height)).toBeLessThan(1);
        }
        await expect(date).toHaveValue(value);
        await expectNoHorizontalOverflow(page);
      }
    }
  }
});

test("E2E-UI-017 実画面の日付選択と終日切替で幅を維持する", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-017
  await login(page, getCredentialsOrSkip());
  for (const width of [320, 390, 430, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const widths: number[] = [];
    for (const feature of ["expenses", "tasks", "habits"]) {
      await page.goto(`/carbohydratepro/${feature}/`);
      const control = page.locator(".date-filter-control");
      await expect(control).toBeVisible();
      widths.push((await control.boundingBox())!.width);
      await expectNoHorizontalOverflow(page);
    }
    expect(Math.max(...widths) - Math.min(...widths)).toBeLessThan(1);
    await page.goto("/carbohydratepro/tasks/");
    await page.getByRole("button", { name: /新規タスク/ }).click();
    const modal = page.locator("#createTaskModal");
    await expect(modal.getByRole("heading", { name: "タスク新規登録" })).toBeVisible();
    const start = modal.locator('[name="start_date"]');
    const end = modal.locator('[name="end_date"]');
    await start.fill("2026-09-27");
    await end.fill("2026-09-28");
    let initialWidth = 0;
    for (const allDay of [false, true, false]) {
      await modal.locator('[name="all_day"]').setChecked(allDay);
      const a = (await start.boundingBox())!;
      const b = (await end.boundingBox())!;
      if (!initialWidth) initialWidth = a.width;
      expect(a.width).toBe(initialWidth);
      expect(a.width).toBe(b.width);
      expect(a.x).toBe(b.x);
      await expect(start).toHaveValue("2026-09-27");
      await expect(end).toHaveValue("2026-09-28");
      await expectNoHorizontalOverflow(page);
    }
    await modal.getByRole("button", { name: "キャンセル", exact: true }).click();
    await expect(modal).toBeHidden();
  }
});
