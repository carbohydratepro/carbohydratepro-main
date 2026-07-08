import { expect, test } from "../fixtures/base";

test.describe("レスポンシブ", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("E2E-RESP-001 390px幅で主要導線を操作できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-resp-001
    await page.goto("/top/");

    await expect(page.getByRole("heading", { name: "Life Management" })).toBeVisible();
    await page.getByRole("button", { name: "Toggle navigation" }).click();

    const navigation = page.locator("#navbarSupportedContent");
    await expect(navigation.getByRole("link", { name: "デモ" })).toBeVisible();
    await expect(navigation.getByRole("link", { name: "ログイン" })).toBeVisible();
    await expect(navigation.getByRole("link", { name: "サインアップ" })).toBeVisible();

    await navigation.getByRole("link", { name: "デモ" }).click();
    await expect(page).toHaveURL(/\/demo\/expenses\/?$/);
    await expect(page.getByText("デモモード")).toBeVisible();
  });

  test("E2E-RESP-002 390px幅でボトムタブから各画面へ遷移できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-resp-002
    await page.goto("/demo/home/");

    const bottomnav = page.locator(".app-bottomnav");
    await expect(bottomnav.getByRole("link", { name: "ホーム" })).toBeVisible();

    // ボトムタブから家計簿へ
    await bottomnav.getByRole("link", { name: "家計簿" }).click();
    await expect(page).toHaveURL(/\/demo\/expenses\/?$/);

    // 「その他」メニューからメモへ
    await page.getByRole("button", { name: "その他のメニュー" }).click();
    const memoLink = page.locator(".app-bottomnav").getByRole("link", { name: "メモ" });
    await expect(memoLink).toBeVisible();
    await memoLink.click();
    await expect(page).toHaveURL(/\/demo\/memos\/?$/);

    // モバイルではサイドバーが表示されない
    await expect(page.locator(".app-sidebar")).toBeHidden();
  });
});
