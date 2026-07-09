import { expect, test } from "../fixtures/base";

const demoPages = [
  { path: "/demo/home/", text: "ホーム" },
  { path: "/demo/expenses/", text: "家計簿" },
  { path: "/demo/tasks/", text: "スケジュール" },
  { path: "/demo/board/", text: "一時タスク" },
  { path: "/demo/habits/", text: "習慣" },
  { path: "/demo/memos/", text: "メモ" },
  { path: "/demo/shopping/", text: "買い物" },
];

test.describe("デモモード", () => {
  test("E2E-DEMO-001 デモトップから各デモ機能へ遷移できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-demo-001
    await page.goto("/demo/");
    await expect(page).toHaveURL(/\/demo\/expenses\/?$/);
    await expect(page.getByText("デモモード")).toBeVisible();

    for (const demoPage of demoPages) {
      await page.goto(demoPage.path);
      await expect(page.getByText("デモモード")).toBeVisible();
      await expect(page.locator("body")).toContainText(demoPage.text);
    }

    await expect(page.getByRole("link", { name: /サインアップ/ }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /ログイン/ }).first()).toBeVisible();
  });

  test("E2E-DEMO-002 デモの登録操作はサインアップモーダルを出し、エラー通知を出さない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-demo-002
    let nativeDialog: string | null = null;
    const consoleErrors: string[] = [];
    page.on("dialog", (d) => { nativeDialog = d.message(); void d.dismiss(); });
    page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });

    await page.goto("/demo/expenses/");
    await page.getByRole("button", { name: /収支登録/ }).click();

    // デモ用サインアップモーダルが表示される
    await expect(page.locator("#demoSignupModal")).toBeVisible();
    // エラーalert・コンソールエラーは出ない
    expect(nativeDialog).toBeNull();
    expect(consoleErrors).toEqual([]);
  });
});
