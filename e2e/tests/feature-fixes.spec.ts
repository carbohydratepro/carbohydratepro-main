import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";

test.describe("2026-07-26 機能修正", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  test("E2E-FIXES-001 詳細絞り込みと週の開始曜日を操作できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-fixes-001
    await page.goto("/carbohydratepro/home/");
    await expect(page.getByText("今日のひとこと")).toBeVisible();
    await expect(page.getByRole("button", { name: "天気を表示" })).toBeVisible();

    await page.goto("/carbohydratepro/expenses/");
    await page.getByRole("button", { name: "検索・絞り込み" }).click();
    await expect(page.getByRole("group", { name: /カテゴリ/ })).toBeVisible();
    await expect(page.getByRole("group", { name: /支払方法/ })).toBeVisible();
    await expect(page.locator("canvas.chart-filterable").first()).toBeAttached();

    await page.goto("/carbohydratepro/tasks/settings/");
    await page.getByLabel("月曜開始").check({ force: true });
    await Promise.all([
      page.waitForNavigation({ waitUntil: "domcontentloaded" }),
      page.getByRole("button", { name: "保存" }).click(),
    ]);
    await expect(page.getByLabel("月曜開始")).toBeChecked();

    // 他のE2Eケースにセッション設定を残さない。
    await page.getByLabel("日曜開始").check({ force: true });
    await Promise.all([
      page.waitForNavigation({ waitUntil: "domcontentloaded" }),
      page.getByRole("button", { name: "保存" }).click(),
    ]);
  });
});
