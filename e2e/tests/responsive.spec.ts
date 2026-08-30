import { expect, test } from "../fixtures/base";
import { expectNoHorizontalOverflow } from "../fixtures/http";

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

  test("E2E-RESP-003 家計簿グラフを必要な項目だけ展開できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-resp-003
    await page.goto("/demo/expenses/");

    await expect(page.getByRole("button", { name: "収支登録" })).toBeVisible();
    await expect(page.getByRole("button", { name: "選択", exact: true })).toBeHidden();
    await page.getByRole("button", { name: "家計簿のその他の操作" }).click();
    await expect(page.getByRole("button", { name: "選択", exact: true })).toBeVisible();

    await expect(page.locator("#categoryChartPanel")).toBeVisible();
    await expect(page.locator("#dailyExpenseChartPanel")).toBeHidden();
    await page.getByRole("button", { name: "日別支出" }).click();
    await expect(page.locator("#dailyExpenseChartPanel")).toBeVisible();
    await expect(page.locator("#expenseBarChartMobile")).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("E2E-RESP-004 月カレンダーは件数表示から予定一覧を開ける", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-resp-004
    await page.goto("/demo/tasks/");

    const populatedCell = page.locator('.task-calendar-cell:not([data-task-count="0"])').first();
    await expect(populatedCell.locator(".task-mobile-summary")).toBeVisible();
    await expect(populatedCell.locator(".task-list")).toBeHidden();
    await populatedCell.click();
    await expect(page.locator("#dayTasksModal")).toHaveClass(/show/);
    await expectNoHorizontalOverflow(page);
  });

  test("E2E-RESP-005 主要画面は320pxから430pxで横にはみ出さず下部ナビと重ならない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-resp-005
    const targets = ["/demo/home/", "/demo/expenses/", "/demo/tasks/", "/demo/habits/", "/demo/memos/", "/demo/shopping/", "/demo/board/"];

    for (const width of [320, 390, 430]) {
      await page.setViewportSize({ width, height: 844 });
      for (const target of targets) {
        await page.goto(target);
        await expectNoHorizontalOverflow(page);
        await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        const overlap = await page.evaluate(() => {
          const navigation = document.querySelector<HTMLElement>(".app-bottomnav");
          const main = document.querySelector<HTMLElement>(".app-main");
          if (!navigation || !main) return 0;
          const contentBottom = Array.from(main.children)
            .filter((element) => {
              const style = window.getComputedStyle(element);
              return style.display !== "none" && style.position !== "fixed" && element.getBoundingClientRect().height > 0;
            })
            .reduce((bottom, element) => Math.max(bottom, element.getBoundingClientRect().bottom), 0);
          return contentBottom - navigation.getBoundingClientRect().top;
        });
        expect(overlap, `${width}pxの${target}で下部ナビが本文を覆わないこと`).toBeLessThanOrEqual(1);
      }
    }
  });
});
