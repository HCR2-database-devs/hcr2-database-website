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

  const payload = (await response.json()) as T;
  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "error" in payload
        ? String((payload as { error: unknown }).error)
        : typeof payload === "object" && payload !== null && "detail" in payload
          ? String((payload as { detail: unknown }).detail)
        : "Request failed";
    throw new Error(message);
  }
  return payload;
}
