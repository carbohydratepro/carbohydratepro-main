import { expect, test } from "../fixtures/base";
import { dismissMessageDialog, getCredentialsOrSkip, login } from "../fixtures/auth";
import {
  deleteFirstItemContaining,
  firstSelectValue,
  submitAndWaitForNavigation,
  uniqueName,
} from "../fixtures/http";

test.describe("2026-07-26 機能修正", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  test("E2E-FIXES-001 詳細絞り込みと週の開始曜日を操作できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-fixes-001
    await page.goto("/carbohydratepro/home/");
    await expect(page.getByText("今日のひとこと")).toBeVisible();
    await expect(page.getByRole("button", { name: "天気を表示" })).toBeVisible();

    await page.goto("/carbohydratepro/expenses/");
    await page.getByRole("button", { name: "検索・絞り込み" }).click();
    await expect(page.getByRole("group", { name: /^カテゴリ/ })).toBeVisible();
    await expect(page.getByRole("group", { name: /^支払方法/ })).toBeVisible();
    await expect(page.locator("canvas.chart-filterable").first()).toBeAttached();

    const purpose = uniqueName("e2e-chart-filter");
    const date = todayIsoDate();
    const targetMonth = date.slice(0, 7);
    const category = await firstSelectValue(page, "/carbohydratepro/expenses/create/", "category");
    const paymentMethod = await firstSelectValue(page, "/carbohydratepro/expenses/create/", "payment_method");

    await page.goto(`/carbohydratepro/expenses/?view_mode=month&target_date=${targetMonth}`);
    await page.getByRole("button", { name: /収支登録/ }).click();
    const modal = page.locator("#createModal");
    await expect(modal.getByRole("heading", { name: "取引新規登録" })).toBeVisible();
    await modal.locator('[name="date"]').fill(date);
    await modal.locator('[name="amount"]').fill("1234");
    await modal.locator('[name="purpose"]').fill(purpose);
    await modal.locator('[name="transaction_type"]').selectOption("expense");
    await modal.locator('[name="major_category"]').selectOption("variable");
    await modal.locator('[name="category"]').selectOption(category);
    await modal.locator('[name="payment_method"]').selectOption(paymentMethod);
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: /^登録$/ }));

    await expect(page.locator(".summary-money-value").first()).toHaveCSS("text-align", "center");
    const categoryChart = page.locator("#categoryPieChart");
    await expect(categoryChart).toBeAttached();
    await categoryChart.evaluate((canvas) => canvas.setAttribute("data-e2e-preserved", "true"));
    const filterResponse = page.waitForResponse((response) =>
      response.url().includes("/carbohydratepro/expenses/")
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
      if (!chart || chart.data.labels.length === 0 || !chart.options.onClick) {
        throw new Error("カテゴリグラフの絞り込み操作を取得できません。");
      }
      chart.options.onClick(new Event("click"), [{ index: 0, datasetIndex: 0 }]);
    });
    expect((await filterResponse).ok()).toBeTruthy();
    await expect(page).toHaveURL(/[?&]category=\d+/);
    await expect(page.getByText(/絞り込み結果: \d+件/)).toBeVisible();
    await expect(categoryChart).toHaveAttribute("data-e2e-preserved", "true");

    await deleteFirstItemContaining(
      page,
      `/carbohydratepro/expenses/?view_mode=month&target_date=${targetMonth}`,
      purpose,
    );

    await page.goto("/carbohydratepro/tasks/settings/");
    await page.getByText("月曜開始", { exact: true }).click();
    await expect(page.getByLabel("月曜開始")).toBeChecked();
    await Promise.all([
      page.waitForNavigation({ waitUntil: "domcontentloaded" }),
      page.getByRole("button", { name: "保存" }).click(),
    ]);
    await expect(page.getByLabel("月曜開始")).toBeChecked();

    // 他のE2Eケースにセッション設定を残さない。
    await dismissMessageDialog(page);
    await page.getByText("日曜開始", { exact: true }).click();
    await expect(page.getByLabel("日曜開始")).toBeChecked();
    await Promise.all([
      page.waitForNavigation({ waitUntil: "domcontentloaded" }),
      page.getByRole("button", { name: "保存" }).click(),
    ]);
  });
});

function todayIsoDate(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tokyo" }).format(new Date());
}
