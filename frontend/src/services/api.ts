const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers, ...rest } = init ?? {};
  const response = await fetch(`${apiBaseUrl}${path}`, {
    credentials: "include",
    ...rest,
    headers: {
      Accept: "application/json",
      ...headers
    }
  });

  const text = await response.text();

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = JSON.parse(text);
      if (typeof payload === "object" && payload !== null) {
        if ("error" in payload) message = String(payload.error);
        else if ("detail" in payload) message = String(payload.detail);
      }
    } catch {
      if (text && text.length < 200) message = text;
    }
    throw new Error(message);
  }

  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}
