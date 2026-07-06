import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login, openAccountMenu } from "../fixtures/auth";

const authenticatedPages = [
  { name: "ホーム", expectedPath: "/carbohydratepro/home/", text: "ホーム" },
  { name: "家計簿", expectedPath: "/carbohydratepro/expenses/", text: "家計簿" },
  { name: "スケジュール", expectedPath: "/carbohydratepro/tasks/", text: "スケジュール" },
  { name: "一時タスク", expectedPath: "/carbohydratepro/tasks/board/", text: "一時タスク" },
  { name: "習慣", expectedPath: "/carbohydratepro/habits/", text: "習慣" },
  { name: "メモ", expectedPath: "/carbohydratepro/memos/", text: "メモ" },
  { name: "買いものリスト", expectedPath: "/carbohydratepro/shopping/", text: "買い物" },
  // マイページはヘッダーのアカウントメニュー内へ移動した
  { name: "マイページ", expectedPath: /\/my_page\/\d+\/?$/, text: "マイページ", inAccountMenu: true },
];

test.describe("ログイン後ナビゲーション", () => {
  test("E2E-NAV-001 ログイン後の主要ナビから各画面へ遷移できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-nav-001
    const credentials = getCredentialsOrSkip();

    await login(page, credentials);

    for (const target of authenticatedPages) {
      if (target.inAccountMenu) {
        await openAccountMenu(page);
      }
      // ナビ項目はダッシュボードのカード内リンク（「家計簿へ」等）と区別するため完全一致で選択する。
      // アカウントメニュー内はアイコンのCSS生成文字が名前に含まれるため部分一致にする。
      const link = target.inAccountMenu
        ? page.getByRole("link", { name: target.name })
        : page.getByRole("link", { name: target.name, exact: true });
      await link.click();

      if (typeof target.expectedPath === "string") {
        await expect(page).toHaveURL(new RegExp(`${target.expectedPath.replaceAll("/", "\\/")}$`));
      } else {
        await expect(page).toHaveURL(target.expectedPath);
      }

      await expect(page.locator("body")).toContainText(target.text);
    }
  });
});
