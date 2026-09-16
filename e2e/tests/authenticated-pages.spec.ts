import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { expectNoHorizontalOverflow, expectVisibleControlsHaveNames } from "../fixtures/http";

const authenticatedPages = [
  { id: "E2E-HOME-001", path: "/carbohydratepro/home/", text: "ホーム" },
  { id: "E2E-EXPENSES-001", path: "/carbohydratepro/expenses/", text: "家計簿" },
  { id: "E2E-EXPENSES-SET-001", path: "/carbohydratepro/expenses/settings/", text: "支払方法" },
  { id: "E2E-RECURRING-001", path: "/carbohydratepro/expenses/recurring/", text: "定期支払い" },
  { id: "E2E-TASK-001", path: "/carbohydratepro/tasks/", text: "スケジュール" },
  { id: "E2E-TASK-SET-001", path: "/carbohydratepro/tasks/settings/", text: "ラベル" },
  { id: "E2E-BOARD-001", path: "/carbohydratepro/tasks/board/", text: "一時タスク" },
  { id: "E2E-HABIT-001", path: "/carbohydratepro/habits/", text: "習慣" },
  { id: "E2E-HABIT-LIST-001", path: "/carbohydratepro/habits/list/", text: "習慣" },
  { id: "E2E-MEMO-001", path: "/carbohydratepro/memos/", text: "メモ" },
  { id: "E2E-MEMO-SET-001", path: "/carbohydratepro/memos/settings/", text: "種別" },
  { id: "E2E-SHOPPING-001", path: "/carbohydratepro/shopping/", text: "買い物" },
  { id: "E2E-COOKING-PAGE-001", path: "/carbohydratepro/cooking/", text: "料理記録" },
  { id: "E2E-COOKING-PAGE-002", path: "/carbohydratepro/cooking/new/", text: "料理を登録" },
  { id: "E2E-CONTACT-001", path: "/carbohydratepro/contact/", text: "お問い合わせ" },
];

test.describe("認証後ページ表示", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  for (const target of authenticatedPages) {
    test(`${target.id} 認証後ページが表示できる: ${target.path}`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#authenticated-pages
      await page.goto(target.path);
      await expect(page.locator("body")).toContainText(target.text);
      await expectNoHorizontalOverflow(page);
      await expectVisibleControlsHaveNames(page);
    });
  }

  test("E2E-FILTER-001 主要一覧の検索・表示条件がURLに反映される", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#filters-and-search
    await page.goto("/carbohydratepro/expenses/?view_mode=year&target_date=2026&search=e2e&transaction_type=expense&sort_by=amount_desc&per_page=10");
    await expect(page).toHaveURL(/view_mode=year/);
    await expect(page.locator("body")).toContainText("検索");

    await page.goto("/carbohydratepro/memos/?search=e2e&favorite=true&per_page=10");
    await expect(page).toHaveURL(/favorite=true/);
    await expect(page.locator("body")).toContainText("検索");

    await page.goto("/carbohydratepro/shopping/?search=e2e");
    await expect(page).toHaveURL(/search=e2e/);
    await expect(page.locator("body")).toContainText("買い物");
  });

  test("E2E-UI-012 設定と料理フォームはスマホ幅で操作できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-ui-012
    for (const width of [320, 390, 430]) {
      await page.setViewportSize({ width, height: 844 });
      for (const path of ["expenses/settings/", "tasks/settings/", "memos/settings/", "cooking/new/"]) {
        await page.goto(`/carbohydratepro/${path}`);
        await expectNoHorizontalOverflow(page);
        await expectVisibleControlsHaveNames(page);
      }
    }
    await page.goto("/carbohydratepro/memos/settings/");
    await page.getByRole("button", { name: "E2Eメモを編集", exact: true }).click();
    await expect(page.getByRole("heading", { name: "種別を編集", exact: true })).toBeVisible();
    await expectNoHorizontalOverflow(page);
    await page.goto("/carbohydratepro/expenses/settings/");
    await page.getByRole("button", { name: "E2E現金を編集", exact: true }).click();
    await expect(page.getByRole("heading", { name: "支払方法の編集", exact: true })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });
});
