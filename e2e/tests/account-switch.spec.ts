import { Locator, Page } from "@playwright/test";

import { expect, test } from "../fixtures/base";
import {
  dismissMessageDialog,
  getCredentialsOrSkip,
  getSecondaryCredentialsOrSkip,
  login,
  logout,
  openAccountMenu,
} from "../fixtures/auth";

// アカウント編集ページで対象メールアドレスの行を取得する
function accountRow(page: Page, email: string): Locator {
  return page.locator("#account-remove .list-group-item", { hasText: email });
}

// アカウント追加フォームからサブアカウントを連携する（現在アカウントはサブに切り替わる）
async function addSecondaryAccount(page: Page, email: string, password: string): Promise<void> {
  await page.goto("/accounts/add/");
  await page.getByLabel("メールアドレス").fill(email);
  await page.getByLabel("パスワード").fill(password);
  await page.getByRole("button", { name: "追加して切り替え" }).click();
  await expect(page).toHaveURL(/\/carbohydratepro\/home\/?$/);
  await expect(page.getByText(/に切り替えました/)).toBeVisible();
}

// 後片付け: 対象メールアドレスの連携を解除する（未連携なら何もしない）
async function unlinkAccount(page: Page, email: string): Promise<void> {
  await page.goto("/accounts/edit/");
  const row = accountRow(page, email);
  if ((await row.count()) === 0) {
    return;
  }
  page.once("dialog", (dialog) => {
    void dialog.accept();
  });
  await row.getByRole("button", { name: "解除" }).click();
  await expect(accountRow(page, email)).toHaveCount(0);
}

test.describe("複数アカウント切替", () => {
  test("E2E-ACC-001 アカウントを追加して相互に切り替え、解除できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-acc-001
    const main = getCredentialsOrSkip();
    const secondary = getSecondaryCredentialsOrSkip();
    await login(page, main);

    // ヘッダーのアカウントメニューから追加ページへ遷移できる
    await openAccountMenu(page);
    await page.getByRole("link", { name: "アカウント追加" }).click();
    await expect(page).toHaveURL(/\/accounts\/add\/?$/);
    await expect(page.getByRole("heading", { name: "既存アカウントを追加" })).toBeVisible();

    // サブアカウントを追加すると自動的に切り替わる
    await page.getByLabel("メールアドレス").fill(secondary.email);
    await page.getByLabel("パスワード").fill(secondary.password);
    await page.getByRole("button", { name: "追加して切り替え" }).click();
    await expect(page).toHaveURL(/\/carbohydratepro\/home\/?$/);
    await expect(page.getByText(/に切り替えました/)).toBeVisible();

    // 編集ページ: 現在=サブ、メインは切替候補
    await page.goto("/accounts/edit/");
    await expect(accountRow(page, secondary.email)).toContainText("現在のアカウント");
    await expect(
      accountRow(page, main.email).getByRole("button", { name: "切り替え", exact: true }),
    ).toBeVisible();

    // メインへパスワードなしで切り替えられる
    await accountRow(page, main.email).getByRole("button", { name: "切り替え", exact: true }).click();
    await expect(page).toHaveURL(/\/carbohydratepro\/home\/?$/);
    await expect(page.getByText(/に切り替えました/)).toBeVisible();
    await page.goto("/accounts/edit/");
    await expect(accountRow(page, main.email)).toContainText("現在のアカウント");

    // 後片付け: 連携を解除すると一覧から消える
    await unlinkAccount(page, secondary.email);
  });

  test("E2E-ACC-002 現在のアカウントのみログアウトすると連携アカウントへ自動切替する", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-acc-002
    const main = getCredentialsOrSkip();
    const secondary = getSecondaryCredentialsOrSkip();
    await login(page, main);
    await addSecondaryAccount(page, secondary.email, secondary.password);

    // 現在のアカウント（サブ）のみログアウト → メインへ自動切替
    await dismissMessageDialog(page);
    await openAccountMenu(page);
    await page.getByRole("button", { name: "ログアウト" }).click();
    await expect(page).toHaveURL(/\/carbohydratepro\/home\/?$/);
    await expect(page.getByText(/現在のアカウントからログアウトし、.*に切り替えました/)).toBeVisible();

    // 編集ページ: メインが現在、サブはログアウト済み表示
    await page.goto("/accounts/edit/");
    await expect(accountRow(page, main.email)).toContainText("現在のアカウント");
    await expect(accountRow(page, secondary.email)).toContainText("ログアウト済み");
    await expect(
      accountRow(page, secondary.email).getByRole("button", { name: "ログインして切り替え" }),
    ).toBeVisible();

    // 後片付け: 解除して完全にログアウトするとログイン画面になる
    await unlinkAccount(page, secondary.email);
    await logout(page);
  });
});
