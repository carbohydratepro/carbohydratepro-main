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

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test.describe("未認証アクセス制御", () => {
  for (const path of protectedPages) {
    test(`E2E-SEC-001 未認証では保護ページへアクセスできない: ${path}`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#security-and-access-control
      // next パラメータの / はブラウザにより %2F 表記と / 表記の両方があり得る
      await page.goto(path);
      const encoded = escapeRegExp(encodeURIComponent(path));
      const raw = escapeRegExp(path);
      await expect(page).toHaveURL(new RegExp(`/login/\\?next=(?:${encoded}|${raw})$`));
      await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
    });
  }
});
