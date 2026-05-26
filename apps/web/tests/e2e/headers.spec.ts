import { expect, test } from "@playwright/test";

test("returns security headers on home", async ({ request }) => {
  const response = await request.get("/");

  await expect(response).toBeOK();
  expect(response.headers()["content-security-policy"]).toContain(
    "https://js.stripe.com",
  );
  expect(response.headers()["x-frame-options"]).toBe("DENY");
  expect(response.headers()["referrer-policy"]).toBe(
    "strict-origin-when-cross-origin",
  );
});
