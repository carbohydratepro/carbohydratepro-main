import { expect, test } from "../fixtures/base";
import * as path from "node:path";

for (const touch of [false, true]) {
test.describe(`日付フォーム ${touch ? "タッチ" : "マウス"}`, () => {
test.use({ hasTouch: touch });
test("E2E-UI-016 日付欄の幅と開始終了の配置を揃える", async ({ page }, testInfo) => {
  // Spec: docs/e2e/release-test-spec.md#e2e-ui-016
  // DB不要。実際の共通・機能CSSと、各テンプレートの入力構造を検証する。
  await page.setContent(`<main class="app-main">
    <form class="form-inline"><input aria-label="対象月" type="month" class="form-control form-control-sm date-filter-control"></form>
    <form class="form-inline date-selection-form"><input aria-label="対象日" type="date" class="form-control form-control-sm date-filter-control"></form>
    <div class="date-nav"><input aria-label="習慣の日付" type="date" class="date-picker-input date-filter-control"></div>
    </main><div class="modal" style="display:block;position:relative">
    <div class="modal-dialog"><div class="modal-content"><div class="modal-body">
    ${["開始", "終了"].map(label => `<div class="datetime-row mb-2"><span class="datetime-label">${label}</span>
      <input aria-label="${label}日" type="date" value="2026-09-23" class="form-control">
      <div class="time-field"><div class="time-picker-wrapper d-inline-flex align-items-center">
        <select aria-label="${label}時" class="form-control form-control-sm time-hour-select"><option>09</option></select>:
        <select aria-label="${label}分" class="form-control form-control-sm time-minute-select"><option>00</option></select>
      </div></div></div>`).join("")}
    </div></div></div></div>`);
  await page.addStyleTag({ url: "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" });
  for (const file of ["styles.css", "task.css", "ui-components.css"]) {
    await page.addStyleTag({ path: path.resolve("static/app", file) });
  }
  for (const width of [320, 390, 430, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const filterWidths = await Promise.all(["対象月", "対象日", "習慣の日付"].map(async name => (await page.getByLabel(name).boundingBox())!.width));
    expect(new Set(filterWidths).size).toBe(1);
    const start = page.getByLabel("開始日");
    const end = page.getByLabel("終了日");
    await page.locator(".time-field").evaluateAll(elements => elements.forEach(el => { (el as HTMLElement).style.display = ""; }));
    const originalWidth = (await start.boundingBox())!.width;
    expect((await page.getByLabel("開始時").boundingBox())!.height).toBe((await start.boundingBox())!.height);
    if (width === 390) await page.screenshot({ path: testInfo.outputPath("date-controls.png") });
    for (const hidden of [false, true]) {
      await page.locator(".time-field").evaluateAll((elements, hide) => elements.forEach(el => { (el as HTMLElement).style.display = hide ? "none" : ""; }), hidden);
      const a = (await start.boundingBox())!;
      const b = (await end.boundingBox())!;
      expect(a.width).toBe(b.width);
      expect(a.width).toBe(originalWidth);
      expect(a.x).toBe(b.x);
      expect(a.width).toBeGreaterThan(150);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
  }
});
});
}
