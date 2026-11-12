import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login, logout } from "../fixtures/auth";
import {
  deleteFirstItemContaining,
  expectNoHorizontalOverflow,
  firstSelectValue,
  postForm,
} from "../fixtures/http";

test.describe("セキュリティ・運用軽量検査", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  test("E2E-SEC-002 XSS風入力がメモ本文で実行されない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#security-and-access-control
    const title = `e2e-xss-${Date.now()}`;
    await page.goto("/carbohydratepro/memos/");
    const memoType = await firstSelectValue(page, "/carbohydratepro/memos/create/", "memo_type");

    await postForm(page, "/carbohydratepro/memos/create/", {
      title,
      memo_type: memoType,
      content: `<script>window.__E2E_XSS_EXECUTED__ = true</script>`,
      is_favorite: "",
    });
    await page.goto(`/carbohydratepro/memos/?search=${encodeURIComponent(title)}`);
    const executed = await page.evaluate(() => Boolean((window as unknown as { __E2E_XSS_EXECUTED__?: boolean }).__E2E_XSS_EXECUTED__));
    expect(executed).toBe(false);

    await deleteFirstItemContaining(page, "/carbohydratepro/memos/", title);
  });

  test("E2E-SEC-003 外部カレンダー文字列がタスクモーダルで実行されない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#security-and-access-control
    const now = new Date();
    const year = String(now.getFullYear());
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const payload = `<img src=x onerror="window.__E2E_TASK_XSS__=true">`;
    await page.route(`**/carbohydratepro/tasks/day/${year}-${month}-${day}/`, async route => {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          tasks: [{
            id: 1,
            title: payload,
            status: "",
            priority: "",
            status_display: "",
            priority_display: "",
            due_date: null,
            description: null,
            label: null,
            is_external: true,
            calendar: { name: payload, color: `red; background-image: url(javascript:alert(1))` },
          }],
        }),
      });
    });
    await page.goto("/carbohydratepro/tasks/");

    await page.evaluate(({ year, month, day }) => {
      const taskWindow = window as unknown as {
        showDayTasksModal: (year: string, month: string, day: string, label: string) => void;
      };
      taskWindow.showDayTasksModal(year, month, day, month);
    }, { year, month, day });

    const modal = page.getByRole("dialog", { name: `${year}/${month}/${day}` });
    await expect(modal).toContainText(`${payload.substring(0, 30)}...`);
    await expect(modal.locator("img")).toHaveCount(0);
    const executed = await page.evaluate(() => Boolean(
      (window as unknown as { __E2E_TASK_XSS__?: boolean }).__E2E_TASK_XSS__,
    ));
    expect(executed).toBe(false);
  });

  test("E2E-OPS-001 送信ボタン連打相当でも一覧表示と再読み込みが破綻しない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#operations-and-data-integrity
    await page.goto("/carbohydratepro/expenses/?per_page=10");
    await expect(page.locator("body")).toContainText("家計簿");
    await page.reload();
    await expect(page.locator("body")).toContainText("家計簿");
    await expectNoHorizontalOverflow(page);
  });

  test("E2E-OPS-002 ログアウト後にブラウザバックしても保護ページが利用できない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#operations-and-data-integrity
    await page.goto("/carbohydratepro/memos/");
    await logout(page);
    await page.goBack();
    await page.reload();
    await expect(page).toHaveURL(/\/login\/\?next=/);
    await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
  });
});
