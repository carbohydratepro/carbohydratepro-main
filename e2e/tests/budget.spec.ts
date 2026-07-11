import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { uniqueName } from "../fixtures/http";

test.describe("予算", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  test("E2E-BUDGET-001 全体予算とカテゴリ予算を設定して消化状況を確認できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-budget-001
    // カテゴリを1件用意（家計簿設定から）
    const categoryName = uniqueName("budget-cat");
    await page.goto("/carbohydratepro/expenses/settings/");
    await page.getByRole("textbox", { name: "新しい使用用途" }).fill(categoryName);
    await page.getByRole("button", { name: "追加" }).nth(1).click();
    await page.waitForLoadState("networkidle");

    // 予算画面へ（家計簿ページのボタン経由）
    await page.goto("/carbohydratepro/budget/");
    await expect(page.getByRole("heading", { name: "予算" })).toBeVisible();

    // 全体予算を設定 → 進捗バーが出る
    await page.locator('form input[name="amount"]').first().fill("120000");
    await page.locator("form").filter({ hasText: /設定|更新/ }).first()
      .getByRole("button", { name: /設定|更新/ }).first().click();
    await page.waitForLoadState("networkidle");
    await expect(page.locator(".progress-bar").first()).toBeVisible();

    // 追加したカテゴリの予算を設定
    const catForm = page.locator("form").filter({ has: page.locator('input[name="category_id"]') })
      .filter({ hasText: "" });
    // カテゴリ名の行のフォームを特定して金額入力
    const row = page.locator(".list-group-item", { hasText: categoryName });
    await row.locator('input[name="amount"]').fill("30000");
    await row.getByRole("button", { name: /設定|更新/ }).click();
    await page.waitForLoadState("networkidle");

    // 設定後、そのカテゴリ行に「/ 30,000円」と進捗バー要素が表示される
    // （新規カテゴリは消化0%のためバー幅は0だが、要素は描画される）
    const rowAfter = page.locator(".list-group-item", { hasText: categoryName });
    await expect(rowAfter).toContainText("30,000円");
    await expect(rowAfter.locator(".progress-bar")).toBeAttached();

    // ダッシュボードにも予算バーが出る
    await page.goto("/carbohydratepro/home/");
    await expect(page.getByText("今月の予算")).toBeVisible();
  });
});
