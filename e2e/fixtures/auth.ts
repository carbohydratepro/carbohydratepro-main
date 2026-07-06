import { Page } from "@playwright/test";

import { expect, test } from "./base";

type Credentials = {
  email: string;
  password: string;
};

export function getConfiguredCredentials(): Credentials | null {
  const email = process.env.E2E_USER_EMAIL;
  const password = process.env.E2E_USER_PASSWORD;

  if (!email || !password) {
    return null;
  }

  return { email, password };
}

export function getCredentialsOrSkip(): Credentials {
  const credentials = getConfiguredCredentials();

  if (!credentials) {
    if (process.env.E2E_ALLOW_AUTH_SKIP === "1") {
      test.skip(true, "認証後フローは E2E_USER_EMAIL/E2E_USER_PASSWORD 未設定のためスキップします。");
    }

    throw new Error("E2E_USER_EMAIL と E2E_USER_PASSWORD を設定してください。スキップを許可する場合だけ E2E_ALLOW_AUTH_SKIP=1 を指定してください。");
  }

  return credentials;
}

export function getSecondaryCredentialsOrSkip(): Credentials {
  const email = process.env.E2E_SECONDARY_USER_EMAIL;
  const password = process.env.E2E_SECONDARY_USER_PASSWORD;

  if (!email || !password) {
    if (process.env.E2E_ALLOW_AUTH_SKIP === "1") {
      test.skip(true, "アカウント切替テストは E2E_SECONDARY_USER_EMAIL/E2E_SECONDARY_USER_PASSWORD 未設定のためスキップします。");
    }

    throw new Error("E2E_SECONDARY_USER_EMAIL と E2E_SECONDARY_USER_PASSWORD を設定してください。スキップを許可する場合だけ E2E_ALLOW_AUTH_SKIP=1 を指定してください。");
  }

  return { email, password };
}

export async function login(page: Page, credentials: Credentials): Promise<void> {
  await page.goto("/login/");
  await page.getByLabel("メールアドレス").fill(credentials.email);
  await page.getByLabel(/パスワード|Password/).fill(credentials.password);
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/carbohydratepro\/expenses\/?$/);
  await expect(page.getByText(/こんにちは！ .* さん/)).toBeVisible();
}

export async function dismissMessageDialog(page: Page): Promise<void> {
  const overlay = page.locator("#messageDialog");
  if (await overlay.isVisible()) {
    await page.keyboard.press("Escape");
    await expect(overlay).toBeHidden();
  }
}

export async function openAccountMenu(page: Page): Promise<void> {
  await dismissMessageDialog(page);
  await page.getByRole("button", { name: "アカウントメニュー" }).click();
  await expect(page.getByRole("link", { name: "アカウント編集" })).toBeVisible();
}

export async function logout(page: Page): Promise<void> {
  await openAccountMenu(page);
  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page).toHaveURL(/\/login\/?$/);
  await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
}
