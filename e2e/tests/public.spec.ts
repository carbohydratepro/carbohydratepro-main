import { expect, test } from "../fixtures/base";
import { expectNoHorizontalOverflow, expectVisibleControlsHaveNames } from "../fixtures/http";

const publicPages = [
  { id: "E2E-PUBLIC-001", path: "/top/", text: "Life Management" },
  { id: "E2E-PUBLIC-002", path: "/login/", text: "ログイン" },
  { id: "E2E-PUBLIC-003", path: "/signup/", text: "サインアップ" },
  { id: "E2E-PUBLIC-004", path: "/password_reset/", text: "パスワード" },
  { id: "E2E-PUBLIC-005", path: "/demo/expenses/", text: "デモモード" },
];

test.describe("公開ページ", () => {
  for (const publicPage of publicPages) {
    test(`${publicPage.id} 公開ページが表示できる: ${publicPage.path}`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#public-and-error-pages
      await page.goto(publicPage.path);
      await expect(page.locator("body")).toContainText(publicPage.text);
      await expectNoHorizontalOverflow(page);
      await expectVisibleControlsHaveNames(page);
    });
  }

  test("E2E-PUBLIC-006 robots.txt と sitemap.xml が公開方針通りに返る", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#public-and-error-pages
    const robots = await page.request.get("/robots.txt");
    expect(robots.ok()).toBeTruthy();
    const robotsText = await robots.text();
    expect(robotsText).toContain("Disallow: /carbohydratepro/");
    expect(robotsText).toContain("Sitemap:");

    const sitemap = await page.request.get("/sitemap.xml");
    expect([200, 301, 302]).toContain(sitemap.status());
  });

  test("E2E-PUBLIC-007 存在しないURLで内部情報を表示しない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#public-and-error-pages
    const response = await page.goto(`/not-found-${Date.now()}/`);
    expect(response?.status()).toBe(404);
    await expect(page.locator("body")).not.toContainText("Traceback");
    await expect(page.locator("body")).not.toContainText("SECRET_KEY");
  });
});
