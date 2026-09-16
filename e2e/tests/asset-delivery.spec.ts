import { expect, test } from "../fixtures/base";

test("E2E-UI-010 静的ファイルは圧縮しハッシュ付きURLだけ長期キャッシュする", async ({ page, request }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-010
  await page.goto("/demo/expenses/");
  const path = await page.locator('script[src*="/app/vendor/chart."]').getAttribute("src");
  expect(path).toMatch(/\.[0-9a-f]{12}\.js$/);
  const hashed = await request.get(path!, { headers: { "Accept-Encoding": "gzip" } });
  expect(hashed.ok()).toBeTruthy();
  expect(hashed.headers()["cache-control"]).toBe("public, max-age=31536000, immutable");
  expect(hashed.headers()["content-encoding"]).toBe("gzip");
  expect(hashed.headers()["vary"]).toContain("Accept-Encoding");
  const plain = await request.get("/static/app/vendor/chart.umd.js");
  expect(plain.headers()["cache-control"]).toBe("no-cache");
  const missing = await request.get("/static/app/not-found.123456789abc.js");
  expect(missing.status()).toBe(404);
  expect(missing.headers()["cache-control"] ?? "").not.toContain("immutable");
});

test("E2E-UI-011 オフライン案内だけを保持し古いアプリキャッシュを片付ける", async ({ page, context }) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-011
  // 登録前に旧キャッシュを準備するためPWA登録スクリプトだけ無効にする。
  await page.route("**/app/pwa*.js", route => route.fulfill({ contentType: "application/javascript", body: "" }));
  await page.goto("/demo/home/");
  await page.evaluate(async () => {
    await caches.open("lm-cache-v1");
    await caches.open("unrelated-test-cache");
    await navigator.serviceWorker.register("/sw.js");
    await navigator.serviceWorker.ready;
  });
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBeTruthy();
  const cached = await page.evaluate(async () => ({
    keys: (await caches.keys()).sort(),
    urls: (await (await caches.open("lm-offline-v2")).keys()).map(request => new URL(request.url).pathname),
  }));
  expect(cached).toEqual({ keys: ["lm-offline-v2", "unrelated-test-cache"], urls: ["/offline/"] });
  await context.setOffline(true);
  try {
    await page.goto("/demo/expenses/");
    await expect(page.getByRole("heading", { name: /オフライン/ })).toBeVisible();
  } finally {
    await context.setOffline(false);
  }
});
