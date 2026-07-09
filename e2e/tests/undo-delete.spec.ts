import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { firstSelectValue, submitAndWaitForNavigation, uniqueName } from "../fixtures/http";

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

  test("E2E-UNDO-003 全削除はアプリ内確認ダイアログで行う（window.confirmを使わない）", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-undo-003
    let nativeDialogFired = false;
    page.on("dialog", (d) => { nativeDialogFired = true; void d.dismiss(); });

    await addCard(page, uniqueName("clear-card"));
    await expect(page.locator("#kanbanBoard .kanban-task-card")).not.toHaveCount(0);

    await page.getByRole("button", { name: /全削除/ }).click();
    // ネイティブconfirmではなくアプリ内ダイアログが出る
    const dialog = page.locator(".app-confirm-dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("button", { name: "すべて削除" })).toBeVisible();
    expect(nativeDialogFired).toBe(false);

    // キャンセルで閉じられる
    await dialog.getByRole("button", { name: "キャンセル" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.locator("#kanbanBoard .kanban-task-card")).not.toHaveCount(0);

    // 確定するとすべて消える
    await page.getByRole("button", { name: /全削除/ }).click();
    await page.locator(".app-confirm-dialog").getByRole("button", { name: "すべて削除" }).click();
    await expect(page.locator("#kanbanBoard .kanban-task-card")).toHaveCount(0);
  });

  test("E2E-UNDO-004 一時タスクの削除操作はaria-label付きボタンである", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-undo-004
    const title = uniqueName("a11y-card");
    await addCard(page, title);
    // 削除要素は <button> でアクセシブル名を持つ
    const deleteBtn = boardCard(page, title).locator("button.kanban-task-delete-overlay");
    await expect(deleteBtn).toHaveCount(1);
    await expect(deleteBtn).toHaveAttribute("aria-label", /削除/);
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

test.describe("選択モードの一括削除", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  async function createMemo(page: import("@playwright/test").Page, title: string): Promise<void> {
    const memoType = await firstSelectValue(page, "/carbohydratepro/memos/create/", "memo_type");
    await page.goto("/carbohydratepro/memos/");
    await page.getByRole("button", { name: /新規メモ作成/ }).click();
    const modal = page.locator("#createMemoModal");
    await expect(modal.getByRole("heading", { name: "メモ新規作成" })).toBeVisible();
    await modal.locator('[name="title"]').fill(title);
    await modal.locator('[name="memo_type"]').selectOption(memoType);
    await modal.locator('[name="content"]').fill("bulk delete test");
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: /^登録$/ }));
  }

  test("E2E-BULK-001 メモを選択モードでまとめて削除・取り消しできる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-bulk-001
    const titleA = uniqueName("bulk-memo-a");
    const titleB = uniqueName("bulk-memo-b");
    await createMemo(page, titleA);
    await createMemo(page, titleB);

    await page.goto("/carbohydratepro/memos/?per_page=100");
    const rowA = page.locator(".bulk-item", { hasText: titleA });
    const rowB = page.locator(".bulk-item", { hasText: titleB });

    // 選択モードに入り、2件を選択
    await page.locator("[data-bulk-toggle]").click();
    await expect(page.locator(".bulk-action-bar.show")).toBeVisible();
    await rowA.click();
    await rowB.click();
    await expect(page.locator(".bulk-action-count")).toHaveText("2件を選択中");

    // 削除 → 2件が消えてUndoトーストが出る
    await page.locator(".bulk-action-delete").click();
    await expect(rowA).toBeHidden();
    await expect(rowB).toBeHidden();
    await expect(page.locator(".app-toast")).toContainText("2件を削除しました");

    // 元に戻す → 復活
    await page.getByRole("button", { name: "元に戻す" }).click();
    await expect(rowA).toBeVisible();
    await expect(rowB).toBeVisible();

    // 再度選択して削除し、サーバー反映を待ってからリロード → 消えている
    await page.locator("[data-bulk-toggle]").click();
    await rowA.click();
    await rowB.click();
    const done = page.waitForResponse(
      (r) => r.url().includes("/memos/bulk-delete/") && r.request().method() === "POST",
    );
    await page.locator(".bulk-action-delete").click();
    await done;
    await page.reload({ waitUntil: "networkidle" });
    await expect(page.locator(".bulk-item", { hasText: titleA })).toHaveCount(0);
    await expect(page.locator(".bulk-item", { hasText: titleB })).toHaveCount(0);
  });
});
