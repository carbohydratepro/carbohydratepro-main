import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import {
  deleteFirstItemContaining,
  deleteJson,
  expectOkOrRedirect,
  firstSelectValue,
  itemAttributeByText,
  postForm,
  postJson,
  submitAndWaitForNavigation,
  putJson,
  uniqueName,
} from "../fixtures/http";

test.describe("主要CRUDとAPI", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  test("E2E-MEMO-CRUD-001 メモを登録・検索・お気に入り切替・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    const title = uniqueName("e2e-memo");
    const memoType = await firstSelectValue(page, "/carbohydratepro/memos/create/", "memo_type");

    await page.goto("/carbohydratepro/memos/");
    await page.getByRole("button", { name: /新規メモ作成/ }).click();
    const modal = page.locator("#createMemoModal");
    await expect(modal.getByRole("heading", { name: "メモ新規作成" })).toBeVisible();
    await modal.locator('[name="title"]').fill(title);
    await modal.locator('[name="memo_type"]').selectOption(memoType);
    await modal.locator('[name="content"]').fill("Markdown **content**\n特殊文字 <script>alert(1)</script>");
    await modal.locator('[name="is_favorite"]').check();
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: /^登録$/ }));

    await page.goto(`/carbohydratepro/memos/?search=${encodeURIComponent(title)}`);
    await expect(page.getByText(title, { exact: true }).first()).toBeVisible();

    const memoId = await itemAttributeByText(page, ".lp-delete-item", title);
    const favorite = await postForm(page, `/carbohydratepro/memos/toggle-favorite/${memoId}/`, {});
    expect(favorite.ok()).toBeTruthy();

    await deleteFirstItemContaining(page, "/carbohydratepro/memos/", title);
  });

  test("E2E-SHOPPING-CRUD-001 買い物を登録・検索・購入済み切替・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    const title = uniqueName("e2e-shopping");

    await page.goto("/carbohydratepro/shopping/");
    await page.getByRole("button", { name: /追加/ }).click();
    const modal = page.locator("#createShoppingModal");
    await expect(modal.getByRole("heading", { name: "商品新規追加" })).toBeVisible();
    await modal.locator('[name="title"]').fill(title);
    await modal.locator('[name="frequency"]').selectOption("one_time");
    await modal.locator('[name="price"]').fill("120");
    await modal.locator('[name="remaining_count"]').fill("0");
    await modal.locator('[name="threshold_count"]').fill("0");
    await modal.locator('[name="memo"]').fill("E2E temporary item");
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: /^登録$/ }));

    await page.goto(`/carbohydratepro/shopping/?search=${encodeURIComponent(title)}`);
    await expect(page.getByText(title)).toBeVisible();

    const itemId = await itemAttributeByText(page, ".lp-delete-item", title);
    const toggle = await postForm(page, `/carbohydratepro/shopping/toggle-check/${itemId}/`, {});
    expect(toggle.ok()).toBeTruthy();

    await deleteFirstItemContaining(page, "/carbohydratepro/shopping/", title);
  });

  test("E2E-TASK-CRUD-001 終日タスクを登録・日表示で確認・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    const title = uniqueName("e2e-task");
    const date = todayIsoDate();

    await page.goto("/carbohydratepro/tasks/");
    await page.getByRole("button", { name: /新規タスク登録/ }).click();
    const modal = page.locator("#createTaskModal");
    await expect(modal.getByRole("heading", { name: "タスク新規登録" })).toBeVisible();
    await modal.locator('[name="title"]').fill(title);
    await modal.locator('[name="start_date"]').fill(date);
    await modal.locator('[name="end_date"]').fill(date);
    await modal.locator('[name="all_day"]').check();
    await modal.locator('[name="priority"]').selectOption("medium");
    await modal.locator('[name="status"]').selectOption("not_started");
    await modal.locator('[name="description"]').fill("E2E all day task");
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: /^登録$/ }));

    await page.goto(`/carbohydratepro/tasks/?view_mode=day&target_date=${date}`);
    await expect(page.getByText(title).first()).toBeVisible();

    const taskId = await page.locator("[data-task-id]", { hasText: title }).first().getAttribute("data-task-id");
    expect(taskId).toBeTruthy();
    const deleted = await postForm(page, `/carbohydratepro/tasks/delete/${taskId}/`, {});
    await expectOkOrRedirect(deleted);
  });

  test("E2E-HABIT-CRUD-001 習慣を登録・達成切替・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    const title = uniqueName("e2e-habit");

    await page.goto("/carbohydratepro/habits/list/");
    await page.getByRole("button", { name: /習慣を追加/ }).click();
    const modal = page.locator("#addHabitModal");
    await expect(modal.getByRole("heading", { name: /習慣を追加/ })).toBeVisible();
    await modal.locator("#addTitle").fill(title);
    await modal.locator("#addFrequency").selectOption("daily");
    await modal.locator("#addCoefficient").evaluate((element) => {
      const input = element as HTMLInputElement;
      input.value = "3";
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: /追加/ }));

    await page.goto("/carbohydratepro/habits/list/");
    await expect(page.getByText(title)).toBeVisible();
    const habitId = await itemAttributeByText(page, ".lp-delete-item", title, "data-habit-id");

    await page.goto("/carbohydratepro/habits/");
    const toggle = await postForm(page, "/carbohydratepro/habits/toggle/", {
      habit_id: habitId ?? "",
      date: todayIsoDate(),
      coefficient: "3",
    });
    expect(toggle.ok()).toBeTruthy();

    await page.goto("/carbohydratepro/habits/list/");
    const deleted = await postForm(page, `/carbohydratepro/habits/delete/${habitId}/`, {});
    await expectOkOrRedirect(deleted);
    await page.goto("/carbohydratepro/habits/list/");
    await expect(page.getByText(title)).toHaveCount(0);
  });

  test("E2E-EXPENSES-CRUD-001 家計簿の取引を登録・検索・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    const purpose = uniqueName("e2e-expense");
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

    await page.goto(
      `/carbohydratepro/expenses/?view_mode=month&target_date=${targetMonth}&search=${encodeURIComponent(purpose)}`,
    );
    await expect(page.getByText(purpose, { exact: true }).first()).toBeVisible();

    await deleteFirstItemContaining(page, `/carbohydratepro/expenses/?view_mode=month&target_date=${targetMonth}`, purpose);
  });

  test("E2E-RECURRING-CRUD-001 定期支払いを登録・有効状態切替・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    const purpose = uniqueName("e2e-recurring");
    const category = await firstSelectValue(page, "/carbohydratepro/expenses/recurring/create/", "category");
    const paymentMethod = await firstSelectValue(page, "/carbohydratepro/expenses/recurring/create/", "payment_method");

    await page.goto("/carbohydratepro/expenses/recurring/create/");
    await expect(page.getByRole("heading", { name: "定期支払いの新規登録" })).toBeVisible();
    await page.locator('[name="purpose"]').fill(purpose);
    await page.locator('[name="amount"]').fill("9876");
    await page.locator('[name="transaction_type"]').selectOption("expense");
    await page.locator('[name="major_category"]').selectOption("fixed");
    await page.locator('[name="category"]').selectOption(category);
    await page.locator('[name="payment_method"]').selectOption(paymentMethod);
    await page.locator('[name="purpose_description"]').fill("E2E recurring payment");
    await page.locator('[name="frequency"]').selectOption("daily");
    await submitAndWaitForNavigation(page, page.getByRole("button", { name: /^登録$/ }));

    await expect(page).toHaveURL(/\/carbohydratepro\/expenses\/recurring\/?$/);
    await expect(page.getByText(purpose, { exact: true }).first()).toBeVisible();

    const recurringId = await itemAttributeByText(page, ".lp-delete-item", purpose);
    const toggle = await postForm(page, `/carbohydratepro/expenses/recurring/toggle/${recurringId}/`, {});
    await expectOkOrRedirect(toggle);

    await deleteFirstItemContaining(page, "/carbohydratepro/expenses/recurring/", purpose);
  });

  test("E2E-BOARD-CRUD-001 一時タスクのセットとカードをAPIで登録・更新・削除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#crud-and-api
    await page.goto("/carbohydratepro/tasks/board/");
    const setName = uniqueName("e2e-set");
    const taskTitle = uniqueName("e2e-card");

    const createdSet = await postJson(page, "/carbohydratepro/tasks/board/api/sets/", { name: setName });
    expect(createdSet.status()).toBe(201);
    const setBody = await createdSet.json();

    const createdTask = await postJson(page, "/carbohydratepro/tasks/board/api/", {
      title: taskTitle,
      status: "todo",
      set_id: setBody.id,
    });
    expect(createdTask.status()).toBe(201);
    const taskBody = await createdTask.json();

    const updatedTask = await putJson(page, `/carbohydratepro/tasks/board/api/${taskBody.id}/`, {
      title: `${taskTitle}-updated`,
      status: "doing",
    });
    expect(updatedTask.ok()).toBeTruthy();

    const deletedTask = await deleteJson(page, `/carbohydratepro/tasks/board/api/${taskBody.id}/`);
    expect(deletedTask.ok()).toBeTruthy();
    const deletedSet = await deleteJson(page, `/carbohydratepro/tasks/board/api/sets/${setBody.id}/`);
    expect(deletedSet.ok()).toBeTruthy();
  });
});

function todayIsoDate(): string {
  // 画面はJSTで動くため、UTCではなくJSTの日付を使う（深夜帯の日付ずれ防止）
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tokyo" }).format(new Date());
}
