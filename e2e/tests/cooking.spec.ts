import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import { expectOkOrRedirect, postForm, submitAndWaitForNavigation, uniqueName } from "../fixtures/http";

test.describe("料理記録", () => {
  test("E2E-COOKING-001 手順付き料理を登録し今日の作成を記録できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-cooking-001
    await login(page, getCredentialsOrSkip());
    const title = uniqueName("e2e-cooking");

    await page.goto("/carbohydratepro/cooking/new/");
    await page.getByLabel("料理名").fill(title);
    await page.getByLabel("材料リスト").fill("鶏肉 300g\n玉ねぎ 1個");
    await page.getByLabel("手順ごと").check();

    const visibleSteps = page.locator("[data-step-form]:not(.d-none)");
    await expect(visibleSteps).toHaveCount(1);
    await visibleSteps.nth(0).getByLabel("手順内容").fill("材料を切る");
    await page.getByRole("button", { name: "手順を追加" }).click();
    await expect(visibleSteps).toHaveCount(2);
    await visibleSteps.nth(1).getByLabel("手順内容").fill("弱火で煮込む");

    await submitAndWaitForNavigation(page, page.getByRole("button", { name: "登録する" }));
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.getByText("材料を切る")).toBeVisible();
    await page.getByRole("button", { name: /次へ/ }).click();
    await expect(page.getByText("弱火で煮込む")).toBeVisible();

    await submitAndWaitForNavigation(page, page.getByRole("button", { name: /今日作った/ }));
    await expect(page.getByText("累計作成回数").locator("..")).toContainText("1");

    await page.goto(`/carbohydratepro/cooking/?search=${encodeURIComponent(title)}`);
    await expect(page.getByText(title, { exact: true })).toBeVisible();

    const detailLink = page.getByRole("link", { name: new RegExp(title) });
    const href = await detailLink.getAttribute("href");
    const dishId = href?.match(/\/cooking\/(\d+)\//)?.[1];
    expect(dishId).toBeTruthy();
    const deleted = await postForm(page, `/carbohydratepro/cooking/${dishId}/delete/`, {});
    await expectOkOrRedirect(deleted);
  });
});
