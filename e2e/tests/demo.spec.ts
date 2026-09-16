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

  test("E2E-DEMO-003 デモ家計簿で比較・絞り込み・年表示を操作できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-demo-003
    await page.goto("/demo/expenses/?view_mode=month&target_date=2026-03");

    await page.getByRole("button", { name: "先月・全期間平均と比較" }).click();
    await expect(page.locator("#expenseComparisonPanel")).toBeVisible();
    await expect(page.locator("#expenseComparisonChart")).toBeAttached();
    await expect(page.getByText("記録のある3か月")).toBeVisible();

    const categoryChart = page.locator("#categoryPieChartPC");
    await expect(categoryChart).toBeVisible();
    await categoryChart.evaluate((canvas) => canvas.setAttribute("data-e2e-preserved", "true"));
    const filterResponse = page.waitForResponse((response) =>
      response.url().includes("/demo/expenses/")
      && response.request().headers()["x-requested-with"] === "XMLHttpRequest",
    );
    await categoryChart.evaluate((canvas) => {
      type BrowserChart = {
        data: { labels: string[] };
        options: {
          onClick?: (event: unknown, elements: Array<{ index: number; datasetIndex: number }>) => void;
        };
      };
      const chartApi = (window as unknown as {
        Chart: { getChart: (target: HTMLCanvasElement) => BrowserChart | undefined };
      }).Chart;
      const chart = chartApi.getChart(canvas as HTMLCanvasElement);
      if (!chart?.options.onClick || chart.data.labels.length === 0) {
        throw new Error("デモカテゴリグラフの絞り込み操作を取得できません。");
      }
      chart.options.onClick(new Event("click"), [{ index: 0, datasetIndex: 0 }]);
    });
    expect((await filterResponse).ok()).toBeTruthy();
    await expect(page).toHaveURL(/[?&]category=\d+/);
    await expect(page.getByText(/絞り込み結果: \d+件/)).toBeVisible();
    await expect(categoryChart).toHaveAttribute("data-e2e-preserved", "true");

    await page.goto("/demo/expenses/?view_mode=year&target_date=2026");
    await expect(page.locator("#monthlyBarChart")).toBeAttached();
    await expect(page.getByText("2026年 のサマリー")).toBeVisible();
  });
});
