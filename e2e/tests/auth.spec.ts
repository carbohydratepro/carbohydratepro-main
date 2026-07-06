import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login, logout, openAccountMenu } from "../fixtures/auth";
import { uniqueName } from "../fixtures/http";

test.describe("認証", () => {
  test("E2E-AUTH-002 ログイン失敗時に分かりやすいエラーが表示される", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-auth-002
    await page.goto("/login/");

    await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
    await page.getByLabel("メールアドレス").fill(`missing-${Date.now()}@example.invalid`);
    await page.getByLabel(/パスワード|Password/).fill("wrong-password");
    await page.getByRole("button", { name: "ログイン" }).click();

    await expect(page.getByText("メールアドレスとパスワードが一致しません。")).toBeVisible();
    await expect(page).toHaveURL(/\/login\/?$/);
  });

  test("E2E-AUTH-001 ログインできる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-auth-001
    const credentials = getCredentialsOrSkip();

    await login(page, credentials);

    await expect(page.getByRole("heading", { name: "ホーム" })).toBeVisible();
    // マイページはヘッダーのアカウントメニュー内に表示される
    await openAccountMenu(page);
    await expect(page.getByRole("link", { name: "マイページ" })).toBeVisible();
  });

  test("E2E-AUTH-003 ログアウト後に保護ページへ直接アクセスするとログイン画面へ遷移する", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-auth-003
    const credentials = getCredentialsOrSkip();

    await login(page, credentials);
    await logout(page);
    await page.goto("/carbohydratepro/expenses/");

    await expect(page).toHaveURL(/\/login\/\?next=(?:%2F|\/)carbohydratepro(?:%2F|\/)expenses(?:%2F|\/)$/);
    await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
  });

  test("E2E-AUTH-004 サインアップ時にパスワード不一致エラーが表示される", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-auth-004
    const username = uniqueName("e2e-signup");

    await page.goto("/signup/");
    await expect(page.getByRole("heading", { name: "サインアップ" })).toBeVisible();
    await page.getByLabel("ユーザー名").fill(username);
    await page.getByLabel("メールアドレス").fill(`${username}@example.invalid`);
    await page.locator('[name="password1"]').fill("e2e-password-123");
    await page.locator('[name="password2"]').fill("different-password-123");
    await page.getByRole("button", { name: "サインアップ" }).click();

    await expect(page).toHaveURL(/\/signup\/?$/);
    await expect(page.locator('[name="password2"]')).toHaveClass(/is-invalid/);
    await expect(page.getByText(/一致しません/)).toBeVisible();
  });

  test("E2E-AUTH-005 未登録メールのパスワードリセット申請でも完了画面になる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-auth-005
    await page.goto("/password_reset/");
    await expect(page.getByRole("heading", { name: "パスワードリセット申請" })).toBeVisible();
    await page.getByLabel("メールアドレス").fill(`missing-${Date.now()}@example.invalid`);
    await page.getByRole("button", { name: "送信" }).click();

    await expect(page).toHaveURL(/\/password_reset_done\/?$/);
    await expect(page.getByRole("heading", { name: "パスワードリセット申請完了" })).toBeVisible();
    await expect(page.getByText("入力されたメールアドレスが登録されている場合")).toBeVisible();
  });
});
