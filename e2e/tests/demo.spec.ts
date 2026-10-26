import { expect, test } from "../fixtures/base";

const demoPages = [
  { path: "/demo/home/", text: "ホーム" },
  { path: "/demo/expenses/", text: "家計簿" },
  { path: "/demo/tasks/", text: "スケジュール" },
  { path: "/demo/board/", text: "一時タスク" },
  { path: "/demo/habits/", text: "習慣" },
  { path: "/demo/memos/", text: "メモ" },
  { path: "/demo/shopping/", text: "買い物" },
  { path: "/demo/cooking/", text: "料理記録" },
];

test.describe("デモモード", () => {
  for (const width of [1280, 390]) {
    test(`E2E-DEMO-004 各機能の操作はログイン案内のみ表示する (${width}px)`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#e2e-demo-004
      await page.setViewportSize({ width, height: 900 });
      const protectedRequests: string[] = [];
      page.on('request', request => {
        if (new URL(request.url()).pathname.startsWith('/carbohydratepro/')) protectedRequests.push(request.url());
      });
      page.on('dialog', dialog => { throw new Error(`予期しないダイアログ: ${dialog.message()}`); });
      const cases = [
        { path: 'expenses', actions: ['openCreateModal()', "openEditModal('1')"] },
        { path: 'tasks', actions: ['openCreateTaskModal()', 'openEditTaskModal(1)', 'deleteTaskFromList(1)'] },
        { path: 'memos', actions: ['openCreateMemoModal()', "openEditMemoModal('1')", "toggleFavorite('1', document.body)"] },
        { path: 'shopping', actions: ['openCreateShoppingModal()', 'openEditShoppingModal(1)', 'toggleCheck(1)', "updateCount(1, 'remaining', 'decrease')"] },
        { path: 'board', actions: ["addTask('todo')", 'openBoardSetEditor(false)', 'clearAllTasks()', 'deleteCurrentBoardSet()'] },
      ];
      for (const item of cases) {
        await page.goto(`/demo/${item.path}/`);
        for (const action of item.actions) {
          // 操作入口を直接呼び、クリック/ダブルタップ/キーボード共通のガードを検証。
          await page.evaluate(action);
          const popup = page.getByRole('dialog', { name: 'この操作にはログインが必要です' });
          await expect(popup).toBeVisible();
          await expect(page.locator('.modal.show')).toHaveCount(1);
          await expect(page.locator('.app-toast, .app-confirm-overlay, dialog[open]')).toHaveCount(0);
          await popup.getByRole('button', { name: '閉じる' }).click();
          await expect(popup).toBeHidden();
        }
      }
      await page.goto('/demo/habits/');
      await page.getByRole('button', { name: /を達成にする/ }).first().click();
      await expect(page.locator('#demoSignupModal')).toBeVisible();
      await expect(page.locator('.app-toast')).toHaveCount(0);
      expect(protectedRequests).toEqual([]);
    });

    test(`E2E-DEMO-005 料理デモの検索・登録・詳細とナビ (${width}px)`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#e2e-demo-005
      await page.setViewportSize({ width, height: 900 });
      await page.goto('/demo/memos/');
      if (width < 768) await page.getByRole('button', { name: 'その他のメニュー' }).click();
      await page.getByRole('link', { name: '料理記録', exact: true }).filter({ visible: true }).click();
      await expect(page).toHaveURL(/\/demo\/cooking\/$/);
      await page.getByLabel('料理名・材料を検索').fill('鶏肉');
      await page.getByRole('button', { name: '検索', exact: true }).click();
      await expect(page.locator('.cooking-card')).toHaveCount(1);
      await page.getByRole('link', { name: /チキンカレー/ }).click();
      const popup = page.getByRole('dialog', { name: 'この操作にはログインが必要です' });
      await expect(popup).toBeVisible();
      await popup.getByRole('button', { name: '閉じる' }).click();
      await expect(popup).toBeHidden();
      await page.getByRole('link', { name: '料理を登録' }).click();
      await expect(popup).toBeVisible();
      await expect(page.locator('.app-toast')).toHaveCount(0);
      await expect(page).toHaveURL(/\/demo\/cooking\/\?search=/);
    });

    test(`E2E-DEMO-006 フォーム・削除・設定の実操作も案内だけを表示する (${width}px)`, async ({ page }) => {
      // Spec: docs/e2e/release-test-spec.md#e2e-demo-006
      await page.setViewportSize({ width, height: 900 });
      const requests: string[] = [];
      page.on('request', request => {
        if (new URL(request.url()).pathname.startsWith('/carbohydratepro/')) requests.push(request.url());
      });
      page.on('dialog', dialog => { throw new Error(`予期しない確認: ${dialog.message()}`); });
      for (const path of ['/demo/habits/list/', '/demo/settings/expenses/', '/demo/budget/', '/demo/memos/']) {
        await page.goto(path);
        if (path === '/demo/habits/list/') {
          await page.getByRole('button', { name: /習慣を追加/ }).click();
        } else if (path === '/demo/settings/expenses/') {
          await page.getByRole('button', { name: '追加', exact: true }).first().click();
        } else if (path === '/demo/budget/') {
          // submitイベントを直接発火しても、通常の送信ハンドラへ到達しない。
          await page.locator('form[method="post"]').first().evaluate(form => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
        } else {
          await page.getByRole('button', { name: 'Q1振り返りと次期目標の操作', exact: true }).click();
          await page.getByRole('button', { name: '削除する', exact: true }).filter({ visible: true }).click();
        }
        await expect(page.getByRole('dialog', { name: 'この操作にはログインが必要です' })).toBeVisible();
        await expect(page.locator('.modal.show')).toHaveCount(1);
        await expect(page.locator('.app-toast, .app-confirm-overlay')).toHaveCount(0);
      }
      expect(requests).toEqual([]);
    });
  }
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
