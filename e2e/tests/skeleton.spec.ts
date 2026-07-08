import { expect, test } from "../fixtures/base";

test.describe("スケルトンスクリーン", () => {
  test("E2E-UI-001 画面遷移時にスケルトンスクリーンが表示される", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-ui-001
    await page.goto("/demo/home/");

    // 遷移中のDOMはロケーターで直接観測できない（遷移完了待ちになる）ため、
    // 離脱時点でスケルトンが表示されていたかを pagehide で localStorage に記録する
    await page.evaluate(() => {
      window.addEventListener("pagehide", () => {
        const overlay = document.querySelector(".skeleton-overlay.show");
        const shown = overlay !== null && getComputedStyle(overlay).display === "block";
        window.localStorage.setItem("e2e-skeleton-on-leave", shown ? "shown" : "not-shown");
      });
    });

    await page.getByRole("link", { name: "家計簿", exact: true }).click();
    await expect(page).toHaveURL(/\/demo\/expenses\/?$/);

    const flag = await page.evaluate(() => window.localStorage.getItem("e2e-skeleton-on-leave"));
    expect(flag).toBe("shown");

    // 遷移完了後の新しいページにはスケルトンが表示されていない
    await expect(page.locator(".skeleton-overlay.show")).toHaveCount(0);
  });
});
