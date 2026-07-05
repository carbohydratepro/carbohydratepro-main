import { expect, test } from "../fixtures/base";
import { getCredentialsOrSkip, login } from "../fixtures/auth";
import {
  expectOkOrRedirect,
  itemAttributeByText,
  postForm,
  submitAndWaitForNavigation,
  uniqueName,
} from "../fixtures/http";

test.describe("設定とお問い合わせ", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, getCredentialsOrSkip());
  });

  test("E2E-SETTINGS-001 家計簿の支払方法とカテゴリを追加できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#settings-and-contact
    const payment = uniqueName("e2e-pay");
    const purpose = uniqueName("e2e-cat");

    await page.goto("/carbohydratepro/expenses/settings/");
    await page.locator('input[placeholder="新しい支払方法"]').fill(payment);
    await submitAndWaitForNavigation(page, page.getByRole("button", { name: "追加" }).first());
    await expect(page.getByText(payment)).toBeVisible();

    await page.locator('input[placeholder="新しい使用用途"]').fill(purpose);
    await submitAndWaitForNavigation(page, page.getByRole("button", { name: "追加" }).nth(1));

    await expect(page.getByText(payment)).toBeVisible();
    await expect(page.getByText(purpose)).toBeVisible();

    const paymentId = await itemAttributeByText(page, ".lp-delete-modal-item", payment);
    const purposeId = await itemAttributeByText(page, ".lp-delete-modal-item", purpose);
    await expectOkOrRedirect(await postForm(page, "/carbohydratepro/expenses/settings/", {
      payment_id: paymentId,
      delete_payment: "true",
    }));
    await expectOkOrRedirect(await postForm(page, "/carbohydratepro/expenses/settings/", {
      purpose_id: purposeId,
      delete_purpose: "true",
    }));
    await page.goto("/carbohydratepro/expenses/settings/");
    await expect(page.getByText(payment)).toHaveCount(0);
    await expect(page.getByText(purpose)).toHaveCount(0);
  });

  test("E2E-SETTINGS-002 タスクラベルを追加できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#settings-and-contact
    const label = uniqueName("e2e-label");

    await page.goto("/carbohydratepro/tasks/settings/");
    await page.getByRole("button", { name: /新規作成/ }).click();
    const modal = page.locator("#createLabelModal");
    await expect(modal.getByRole("heading", { name: "新しいラベルを作成" })).toBeVisible();
    await modal.locator("#label-name").fill(label);
    await modal.locator("#label-color").evaluate((element) => {
      const input = element as HTMLInputElement;
      input.value = "#6c757d";
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: "作成" }));

    await expect(page.getByText(label)).toBeVisible();
    const labelId = await itemAttributeByText(page, ".lp-delete-modal-item", label);
    await expectOkOrRedirect(await postForm(page, "/carbohydratepro/tasks/settings/", {
      label_id: labelId,
      delete_label: "1",
    }));
    await page.goto("/carbohydratepro/tasks/settings/");
    await expect(page.getByText(label)).toHaveCount(0);
  });

  test("E2E-SETTINGS-003 メモ種別を追加できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#settings-and-contact
    const memoType = uniqueName("e2e-memo-type");

    await page.goto("/carbohydratepro/memos/settings/");
    await page.getByRole("button", { name: /新規作成/ }).click();
    const modal = page.locator("#createMemoTypeModal.modal");
    await expect(modal.getByRole("heading", { name: "新しい種別を作成" })).toBeVisible();
    await modal.locator("#memo-type-name").fill(memoType);
    await modal.locator("#memo-type-color").evaluate((element) => {
      const input = element as HTMLInputElement;
      input.value = "#6c757d";
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await submitAndWaitForNavigation(page, modal.getByRole("button", { name: "作成" }));

    await expect(page.getByText(memoType)).toBeVisible();
    const memoTypeId = await itemAttributeByText(page, ".lp-delete-modal-item", memoType);
    await expectOkOrRedirect(await postForm(page, "/carbohydratepro/memos/settings/", {
      memo_type_id: memoTypeId,
      delete_memo_type: "1",
    }));
    await page.goto("/carbohydratepro/memos/settings/");
    await expect(page.getByText(memoType)).toHaveCount(0);
  });

  test("E2E-CONTACT-CRUD-001 お問い合わせを送信できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#settings-and-contact
    const subject = uniqueName("e2e-contact");

    await page.goto("/carbohydratepro/contact/");
    await page.locator('[name="inquiry_type"]').selectOption("bug");
    await page.getByLabel("件名").fill(subject);
    await page.getByLabel("お問い合わせ内容").fill("E2E contact message\n複数行と特殊文字 <> & を含む");
    await submitAndWaitForNavigation(page, page.getByRole("button", { name: "送信する" }));

    await expect(page.getByText(subject)).toBeVisible();
  });
});
