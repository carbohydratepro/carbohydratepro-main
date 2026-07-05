import { expect, test } from "../fixtures/base";

const protectedPages = [
  "/carbohydratepro/expenses/",
  "/carbohydratepro/expenses/settings/",
  "/carbohydratepro/expenses/recurring/",
  "/carbohydratepro/tasks/",
  "/carbohydratepro/tasks/settings/",
  "/carbohydratepro/tasks/board/",
  "/carbohydratepro/habits/",
  "/carbohydratepro/habits/list/",
  "/carbohydratepro/memos/",
  "/carbohydratepro/memos/settings/",
  "/carbohydratepro/shopping/",
  "/carbohydratepro/contact/",
  "/my_page/1/",
  "/edit/1",
  "/password_change/",
];

test.describe("未認証アクセス制御", () => {
  for (const path of protectedPages) {
    test(`E2E-SEC-001 未認証では保護ページへアクセスできない: ${path}`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#security-and-access-control
      await page.goto(path);
      await expect(page).toHaveURL(new RegExp(`/login/\\?next=${encodeURIComponent(path).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`));
      await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
    });
  }
});
