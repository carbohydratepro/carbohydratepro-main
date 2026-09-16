import { expect, test } from "../fixtures/base";
import { expectNoHorizontalOverflow } from "../fixtures/http";
import type { Page } from "@playwright/test";
import { getCredentialsOrSkip, login } from "../fixtures/auth";

for (const touch of [false, true]) {
  test.describe(`共通ボタン ${touch ? "タッチ" : "PC"}`, () => {
    test.use({ hasTouch: touch, viewport: { width: touch ? 390 : 1440, height: 900 } });
    test(`E2E-UI-013 共通操作の高さと角丸を揃える (${touch})`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#e2e-ui-013
      for (const path of ["expenses", "tasks", "shopping", "memos"]) {
        await page.goto(`/demo/${path}/`);
        const buttons = page.locator(".page-heading-row .btn:visible");
        expect(await buttons.count()).toBeGreaterThan(0);
        for (const button of await buttons.all()) {
          const dimensions = await button.evaluate(el => ({
            height: el.getBoundingClientRect().height,
            radius: getComputedStyle(el).borderRadius,
          }));
          expect(dimensions.height).toBe(touch ? 40 : 36);
          expect(dimensions.radius).toBe("8px");
        }
        await expectNoHorizontalOverflow(page);
      }
    });
  });
}

async function chartIds(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const chartApi = (window as unknown as {
      Chart: { instances: Record<string, { canvas: HTMLCanvasElement }> };
    }).Chart;
    return Object.values(chartApi.instances).map(chart => chart.canvas.id).sort();
  });
}

test("E2E-UI-002 ホームの補助情報は必要なときだけ展開できる", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-002
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/demo/home/");
  expect(await page.locator("html").evaluate(el => getComputedStyle(el).fontSize)).toBe("16.5px");
  const weather = page.getByRole("button", { name: "天気を表示" });
  await expect(weather).toBeHidden();
  const summary = page.getByText("今日のひとこと・天気", { exact: true });
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(weather).toBeVisible();
  await summary.click();
  await expect(weather).toBeHidden();
  await expectNoHorizontalOverflow(page);
});

test("E2E-UI-003 PCの主要画面は共通レイアウトと先行CSSを使用する", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-003
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const [path, asset] of [["expenses", "transaction"], ["tasks", "task"], ["memos", "memo"]]) {
    await page.goto(`/demo/${path}/`);
    await expect(page.getByRole("navigation", { name: "メイン", exact: true })).toBeVisible();
    await expect(page.locator(`head link[href*="/app/${asset}."]`)).toHaveCount(1);
    await expect(page.locator(`body link[href*="/app/${asset}."]`)).toHaveCount(0);
    await expectNoHorizontalOverflow(page);
  }
  await page.goto("/demo/tasks/");
  const calendar = page.locator(".workspace-wide");
  expect((await calendar.boundingBox())?.width).toBeGreaterThan(960);
  await page.goto("/login/");
  expect((await page.locator(".app-main > .container").boundingBox())?.width).toBeLessThanOrEqual(800);
});

test("E2E-UI-004 家計簿は表示するグラフだけ生成し再展開で再生成しない", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-004
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/demo/expenses/?view_mode=month&target_date=2026-03");
  await expect.poll(() => chartIds(page)).toEqual(["categoryPieChart"]);
  const toggle = page.getByRole("button", { name: "日別支出", exact: true });
  await toggle.click();
  await expect(page.locator("#dailyExpenseChartPanel")).toHaveClass(/show/);
  await expect.poll(() => chartIds(page)).toEqual(["categoryPieChart", "expenseBarChartMobile"]);
  const chartIdentity = await page.locator("#expenseBarChartMobile").evaluate(canvas => {
    const chartApi = (window as unknown as {
      Chart: { getChart(canvas: HTMLCanvasElement): { id: string } };
    }).Chart;
    return chartApi.getChart(canvas as HTMLCanvasElement).id;
  });
  await toggle.click();
  await expect(page.locator("#dailyExpenseChartPanel")).toBeHidden();
  await toggle.click();
  await expect(page.locator("#dailyExpenseChartPanel")).toHaveClass(/show/);
  expect(await page.locator("#expenseBarChartMobile").evaluate(canvas => {
    const chartApi = (window as unknown as {
      Chart: { getChart(canvas: HTMLCanvasElement): { id: string } };
    }).Chart;
    return chartApi.getChart(canvas as HTMLCanvasElement).id;
  })).toBe(chartIdentity);

  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect.poll(() => chartIds(page)).toEqual([
    "balanceLineChart", "categoryPieChart", "categoryPieChartPC",
    "expenseBarChart", "expenseBarChartMobile", "majorCategoryChartPC",
  ]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "日別収支推移", exact: true }).click();
  await expect.poll(async () => (await chartIds(page)).includes("balanceLineChartMobile")).toBeTruthy();
  const line = await page.locator("#balanceLineChartMobile").evaluate(canvas => {
    const chartApi = (window as unknown as {
      Chart: { getChart(canvas: HTMLCanvasElement): {
        data: { labels: string[]; datasets: Array<{ data: number[] }> };
        options: { animation: unknown };
      } };
    }).Chart;
    const chart = chartApi.getChart(canvas as HTMLCanvasElement);
    return { labels: chart.data.labels.length, points: chart.data.datasets[0].data.length, animation: chart.options.animation };
  });
  expect(line.points).toBe(line.labels);
  expect(line.animation).toBe(false);
});

test("E2E-UI-005 記録がない月の収支グラフも有限の目盛りで表示する", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-005
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/demo/expenses/?view_mode=month&target_date=2027-01");
  const scale = await page.locator("#balanceLineChart").evaluate(canvas => {
    const chartApi = (window as unknown as {
      Chart: { getChart(canvas: HTMLCanvasElement): {
        data: { datasets: Array<{ data: number[] }> };
        options: { scales: { y: { min: number; max: number; ticks: { stepSize: number } } } };
      } };
    }).Chart;
    const chart = chartApi.getChart(canvas as HTMLCanvasElement);
    const y = chart.options.scales.y;
    return { values: chart.data.datasets[0].data, min: y.min, max: y.max, step: y.ticks.stepSize };
  });
  expect(scale.values).toHaveLength(31);
  expect(scale.values.every(value => value === 0)).toBeTruthy();
  expect([scale.min, scale.max, scale.step].every(Number.isFinite)).toBeTruthy();
  expect(scale.max).toBeGreaterThan(scale.min);
  expect(scale.step).toBeGreaterThan(0);
});

test("E2E-UI-007 家計簿をボタンで絞り込み解除してもグラフと期間は維持する", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-007
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/demo/expenses/?view_mode=month&target_date=2026-03");
  const chart = page.locator("#categoryPieChart");
  await chart.evaluate(canvas => canvas.setAttribute("data-preserved", "yes"));
  const originalIds = await chartIds(page);
  await page.getByText("カテゴリを選ぶ", { exact: true }).click();
  const option = page.locator('[data-chart-filter="category"]').first();
  await option.focus();
  await page.keyboard.press("Enter");
  await expect(option).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText(/絞り込み結果: \d+件/)).toBeVisible();
  await page.getByRole("button", { name: "絞り込みを解除", exact: true }).click();
  await expect(page).toHaveURL(/\?view_mode=month&target_date=2026-03$/);
  await expect(option).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("button", { name: "絞り込みを解除", exact: true })).toHaveCount(0);
  await expect(chart).toHaveAttribute("data-preserved", "yes");
  expect(await chartIds(page)).toEqual(originalIds);
});

test("E2E-UI-008 習慣の期間と達成状態はキーボードで操作できる", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-008
  await login(page, getCredentialsOrSkip());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/carbohydratepro/habits/");
  await page.getByRole("tab", { name: "日", exact: true }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "週", exact: true })).toBeFocused();
  await expect(page.getByRole("tabpanel", { name: "週", exact: true })).toBeVisible();
  await expect(page.getByRole("tabpanel", { name: "日", exact: true })).toHaveCount(0);
  await page.keyboard.press("Home");
  const complete = page.getByRole("button", { name: "E2E毎日の習慣を達成にする", exact: true });
  await complete.focus();
  await page.keyboard.press("Enter");
  const undo = page.getByRole("button", { name: "E2E毎日の習慣を未達成に戻す", exact: true });
  await expect(undo).toHaveAttribute("aria-pressed", "true");
  await undo.focus();
  await page.keyboard.press("Enter");
  await expect(complete).toHaveAttribute("aria-pressed", "false");
  await expectNoHorizontalOverflow(page);
});

test("E2E-UI-009 認証フォームの幅と本文へのスキップリンクを確認する", async ({ page }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-009
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/login/");
    const input = page.getByLabel("メールアドレス", { exact: true });
    await expect(page.getByRole("button", { name: "ログイン", exact: true })).toHaveCSS("font-weight", "500");
    expect((await input.boundingBox())?.width).toBeGreaterThan(width === 320 ? 200 : 260);
    await expectNoHorizontalOverflow(page);
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "本文へ移動", exact: true })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("main")).toBeFocused();
  }
});
