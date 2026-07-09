import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { uniqueName } from "../fixtures/http";

// 一時タスクの削除は誤操作に備えて「元に戻す（Undo）」トーストを出す。
// 削除の発火経路（長押し／ドラッグ）は既存のジェスチャーで、いずれも window.deleteTask を呼ぶ。
// ここでは変更対象の deleteTask の挙動（トースト・復元・本削除）を検証する。
test.describe("削除のUndoトースト", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
    await page.goto("/carbohydratepro/tasks/board/");
    await page.waitForLoadState("networkidle");
  });

  async function addCard(page: import("@playwright/test").Page, title: string): Promise<void> {
    await page.locator("#input-todo").fill(title);
    await page.locator("#col-todo .kanban-add-btn").click();
    // 保存完了（未保存ドット消滅）を待つ
    await expect(page.locator("#kanbanBoard .kanban-task-unsaved-dot")).toHaveCount(0);
  }

  function boardCard(page: import("@playwright/test").Page, title: string) {
    return page.locator("#kanbanBoard .kanban-task-card", { hasText: title });
  }

  async function triggerDelete(page: import("@playwright/test").Page, title: string): Promise<void> {
    await page.evaluate((t) => {
      const cards = Array.from(document.querySelectorAll<HTMLElement>("#kanbanBoard .kanban-task-card"));
      const card = cards.find((c) => c.textContent?.includes(t));
      if (card) {
        (window as unknown as { deleteTask: (id: string) => void }).deleteTask(card.dataset["localId"] ?? "");
      }
    }, title);
  }

  test("E2E-UNDO-001 一時タスク削除がトーストで取り消せる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-undo-001
    const title = uniqueName("undo-card");
    await addCard(page, title);
    await expect(boardCard(page, title)).toHaveCount(1);

    // 削除するとカードが消え、Undoトーストが出る
    await triggerDelete(page, title);
    await expect(boardCard(page, title)).toHaveCount(0);
    const toast = page.locator(".app-toast");
    await expect(toast).toBeVisible();
    await expect(toast).toContainText("削除しました");

    // 「元に戻す」で復元される
    await page.getByRole("button", { name: "元に戻す" }).click();
    await expect(boardCard(page, title)).toHaveCount(1);
    await expect(page.locator("#kanbanBoard .kanban-task-unsaved-dot")).toHaveCount(0);

    // 復元はサーバーにも反映される（リロード後も残る）
    await page.reload({ waitUntil: "networkidle" });
    await expect(boardCard(page, title)).toHaveCount(1);
  });

  test("E2E-UNDO-002 取り消さなければ削除が確定する", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-undo-002
    const title = uniqueName("commit-card");
    await addCard(page, title);
    await expect(boardCard(page, title)).toHaveCount(1);

    // 削除リクエストの完了を待ってから離脱する（実利用では背景で完了する）
    const deleteDone = page.waitForResponse(
      (r) => r.request().method() === "DELETE" && r.url().includes("/tasks/board/api/"),
    );
    await triggerDelete(page, title);
    await expect(boardCard(page, title)).toHaveCount(0);
    await deleteDone;

    // Undoせずリロード → サーバー側でも削除されている
    await page.reload({ waitUntil: "networkidle" });
    await expect(boardCard(page, title)).toHaveCount(0);
  });
});
