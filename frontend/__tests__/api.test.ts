import { loginUser } from "@/lib/api";

function createResponse(status: number, body: unknown): Response {
  const serializedBody = JSON.stringify(body);
  return {
    body: null,
    bodyUsed: false,
    headers: new Headers(),
    ok: status >= 200 && status < 300,
    redirected: false,
    status,
    statusText: "",
    type: "basic",
    url: "",
    bytes: async () => new TextEncoder().encode(serializedBody),
    arrayBuffer: async () => new TextEncoder().encode(serializedBody).buffer,
    blob: async () => new Blob([serializedBody]),
    formData: async () => new FormData(),
    json: jest.fn().mockResolvedValue(body),
    text: async () => serializedBody,
    clone: () => createResponse(status, body),
  };
}

describe("login API retry handling", () => {
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = jest.fn();
    Object.defineProperty(globalThis, "fetch", {
      configurable: true,
      value: fetchMock,
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    delete (globalThis as { fetch?: typeof fetch }).fetch;
  });

  it("uses a 20-second request timeout", async () => {
    fetchMock.mockResolvedValue(
      createResponse(200, { user: { id: "1" }, csrf_token: "token" }),
    );
    const setTimeoutSpy = jest.spyOn(global, "setTimeout");

    await loginUser({ email: "user@example.com", password: "password123" });

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 20_000);
  });

  it(
    "retries timeouts and 504 responses with backoff and notifies the caller",
    async () => {
      fetchMock
        .mockRejectedValueOnce(new DOMException("Request aborted", "AbortError"))
        .mockResolvedValueOnce(createResponse(504, { detail: "Gateway timeout" }))
        .mockResolvedValueOnce(
          createResponse(200, { user: { id: "1" }, csrf_token: "token" }),
        );
      const onRetry = jest.fn();

      await expect(
        loginUser({ email: "user@example.com", password: "password123" }, onRetry),
      ).resolves.toEqual({ user: { id: "1" }, csrf_token: "token" });

      expect(fetchMock).toHaveBeenCalledTimes(3);
      expect(onRetry).toHaveBeenCalledTimes(2);
    },
    10_000,
  );
});
