import { expect, test } from "../fixtures/base";

test.describe("スケルトンスクリーン", () => {
  test.use({ serviceWorkers: "block" });
  test("E2E-UI-001 待ち時間のある画面遷移だけスケルトンを表示する", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-ui-001
    await page.goto("/demo/home/");
    await page.route("**/demo/expenses/", async route => {
      const response = await route.fetch();
      // 遅い回線を再現する。ページ自体のテスト待機には固定sleepを使わない。
      await new Promise(resolve => setTimeout(resolve, 400));
      await route.fulfill({ response });
    });

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

  test("E2E-UI-006 復帰時は表示待ちを取り消し同一画面リンクでは表示しない", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-ui-006
    await page.goto("/demo/expenses/");
    await page.getByRole("link", { name: "記録一覧へ", exact: true }).click();
    await expect(page.locator(".skeleton-overlay.show")).toHaveCount(0);
    const shown = await page.evaluate(async () => {
      const link = document.createElement("a");
      link.href = "/demo/home/";
      document.body.append(link);
      // documentの処理後、実遷移だけを止めて表示遅延と復帰を検証する。
      window.addEventListener("click", event => event.preventDefault(), { once: true });
      link.click();
      const immediate = !!document.querySelector(".skeleton-overlay.show");
      window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
      await new Promise(resolve => setTimeout(resolve, 300));
      link.remove();
      return { immediate, afterRestore: !!document.querySelector(".skeleton-overlay.show") };
    });
    expect(shown).toEqual({ immediate: false, afterRestore: false });
  });
});
