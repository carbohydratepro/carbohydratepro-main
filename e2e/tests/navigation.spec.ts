import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";

const authenticatedPages = [
  { name: "家計簿", expectedPath: "/carbohydratepro/expenses/", text: "家計簿" },
  { name: "スケジュール", expectedPath: "/carbohydratepro/tasks/", text: "スケジュール" },
  { name: "一時タスク", expectedPath: "/carbohydratepro/tasks/board/", text: "一時タスク" },
  { name: "習慣", expectedPath: "/carbohydratepro/habits/", text: "習慣" },
  { name: "メモ", expectedPath: "/carbohydratepro/memos/", text: "メモ" },
  { name: "買いものリスト", expectedPath: "/carbohydratepro/shopping/", text: "買い物" },
  { name: "マイページ", expectedPath: /\/my_page\/\d+\/?$/, text: "マイページ" },
];

test.describe("ログイン後ナビゲーション", () => {
  test("E2E-NAV-001 ログイン後の主要ナビから各画面へ遷移できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-nav-001
    const credentials = getCredentialsOrSkip();

    await login(page, credentials);

    for (const target of authenticatedPages) {
      await page.getByRole("link", { name: target.name }).click();

      if (typeof target.expectedPath === "string") {
        await expect(page).toHaveURL(new RegExp(`${target.expectedPath.replaceAll("/", "\\/")}$`));
      } else {
        await expect(page).toHaveURL(target.expectedPath);
      }

      await expect(page.locator("body")).toContainText(target.text);
    }
  });
});
