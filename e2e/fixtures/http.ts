import { APIResponse, Page, expect, type Locator } from "@playwright/test";

type FormValue = string | number | boolean;

export function uniqueName(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export async function csrfToken(page: Page): Promise<string> {
  const cookies = await page.context().cookies();
  const token = cookies.find((cookie) => cookie.name === "csrftoken")?.value;

  if (!token) {
    throw new Error("CSRF token cookie was not found. Open a Django page containing csrf_token first.");
  }

  return token;
}

export async function postForm(
  page: Page,
  url: string,
  form: Record<string, FormValue>,
): Promise<APIResponse> {
  return page.request.post(url, {
    form: stringifyForm(form),
    headers: {
      "X-CSRFToken": await csrfToken(page),
      Referer: page.url(),
    },
  });
}

export async function postJson(
  page: Page,
  url: string,
  data: Record<string, unknown>,
): Promise<APIResponse> {
  return page.request.post(url, {
    data,
    headers: {
      "X-CSRFToken": await csrfToken(page),
      Referer: page.url(),
    },
  });
}

export async function deleteJson(
  page: Page,
  url: string,
  data: Record<string, unknown> = {},
): Promise<APIResponse> {
  return page.request.delete(url, {
    data,
    headers: {
      "X-CSRFToken": await csrfToken(page),
      Referer: page.url(),
    },
  });
}

export async function putJson(
  page: Page,
  url: string,
  data: Record<string, unknown>,
): Promise<APIResponse> {
  return page.request.put(url, {
    data,
    headers: {
      "X-CSRFToken": await csrfToken(page),
      Referer: page.url(),
    },
  });
}

export async function expectOkOrRedirect(response: APIResponse): Promise<void> {
  expect([200, 201, 204, 302]).toContain(response.status());
}

export async function submitAndWaitForNavigation(page: Page, submitButton: Locator): Promise<void> {
  await Promise.all([
    page.waitForNavigation({ waitUntil: "domcontentloaded" }),
    submitButton.click(),
  ]);
}

export async function firstSelectValue(page: Page, url: string, fieldName: string): Promise<string> {
  const response = await page.request.get(url);
  expect(response.ok(), `${url} が取得できること`).toBeTruthy();
  const html = await response.text();
  const select = matchSelectByName(html, fieldName);

  if (!select) {
    throw new Error(`${url} に name="${fieldName}" の select が見つかりません。`);
  }

  const optionRegex = /<option\b[^>]*value=["']([^"']*)["'][^>]*>/g;
  const values = Array.from(select.matchAll(optionRegex))
    .map((match) => decodeHtml(match[1] ?? ""))
    .filter((value) => value !== "");

  if (values.length === 0) {
    throw new Error(`${url} の name="${fieldName}" に選択可能な option がありません。`);
  }

  return values[0];
}

export async function itemAttributeByText(
  page: Page,
  selector: string,
  text: string,
  attributeName = "data-item-id",
): Promise<string> {
  const item = page.locator(selector, { hasText: text }).first();
  await expect(item, `${text} の対象要素が表示されること`).toBeVisible();
  const value = await item.getAttribute(attributeName);

  if (!value) {
    throw new Error(`${text} の ${attributeName} が見つかりません。`);
  }

  return value;
}

export async function deleteFirstItemContaining(
  page: Page,
  listUrl: string,
  text: string,
): Promise<void> {
  await page.goto(listUrl);
  const item = page.locator(".lp-delete-item", { hasText: text }).first();
  await expect(item, `${text} の削除対象が表示されること`).toBeVisible();
  const deleteUrl = await item.getAttribute("data-delete-url");

  if (!deleteUrl) {
    throw new Error(`${text} の data-delete-url が見つかりません。`);
  }

  const response = await postForm(page, deleteUrl, {});
  await expectOkOrRedirect(response);
  await page.goto(listUrl);
  await expect(page.getByText(text)).toHaveCount(0);
}

export async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    return root.scrollWidth - root.clientWidth;
  });
  expect(overflow, "横方向のはみ出しがないこと").toBeLessThanOrEqual(2);
}

export async function expectVisibleControlsHaveNames(page: Page): Promise<void> {
  const unnamed = await page.evaluate(() => {
    function isVisible(element: Element): boolean {
      const rect = element.getBoundingClientRect();
      const style = window.getComputedStyle(element);
      return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    }

    return Array.from(document.querySelectorAll("button, a, input, select, textarea"))
      .filter((element) => isVisible(element))
      .filter((element) => {
        if (element instanceof HTMLInputElement && element.type === "hidden") return false;
        const ariaLabel = element.getAttribute("aria-label")?.trim();
        const title = element.getAttribute("title")?.trim();
        const text = element.textContent?.trim();
        const labelledBy = element.getAttribute("aria-labelledby")?.trim();
        const id = element.getAttribute("id");
        const label = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`)?.textContent?.trim() : "";
        return !ariaLabel && !title && !text && !labelledBy && !label;
      })
      .map((element) => element.outerHTML.slice(0, 160));
  });

  expect(unnamed, "表示中の主要操作要素に名前があること").toEqual([]);
}

function stringifyForm(form: Record<string, FormValue>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(form).map(([key, value]) => [key, String(value)]),
  );
}

function matchSelectByName(html: string, fieldName: string): string | null {
  const selectRegex = /<select\b[^>]*>[\s\S]*?<\/select>/g;
  for (const match of html.matchAll(selectRegex)) {
    const select = match[0];
    const nameRegex = new RegExp(`\\bname=["']${escapeRegExp(fieldName)}["']`);
    if (nameRegex.test(select)) {
      return select;
    }
  }
  return null;
}

function decodeHtml(value: string): string {
  return value
    .replaceAll("&quot;", "\"")
    .replaceAll("&#x27;", "'")
    .replaceAll("&#39;", "'")
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">");
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
