import { expect, test as base } from "@playwright/test";

const failOnWarning = process.env.E2E_FAIL_ON_CONSOLE_WARN === "1";

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    const consoleIssues: string[] = [];
    const pageErrors: string[] = [];

    page.on("console", (message) => {
      const type = message.type();
      if (type === "error" || (failOnWarning && type === "warning")) {
        consoleIssues.push(`[${type}] ${message.text()}`);
      }
    });

    page.on("pageerror", (error) => {
      pageErrors.push(error.message);
    });

    await use(page);

    if (consoleIssues.length > 0) {
      await testInfo.attach("console-issues", {
        body: consoleIssues.join("\n"),
        contentType: "text/plain",
      });
    }

    if (pageErrors.length > 0) {
      await testInfo.attach("page-errors", {
        body: pageErrors.join("\n"),
        contentType: "text/plain",
      });
    }

    expect(consoleIssues, "ブラウザ console.error が発生していないこと").toEqual([]);
    expect(pageErrors, "ブラウザ pageerror が発生していないこと").toEqual([]);
  },
});

export { expect };
