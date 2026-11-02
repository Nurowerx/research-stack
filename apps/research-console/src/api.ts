export async function api<T>(path: string, body?: unknown): Promise<T> {
  const token = sessionStorage.getItem("nx-token");
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail),
    );
  }
  return response.json() as Promise<T>;
}
export async function exportFile(path: string, name: string) {
  const token = sessionStorage.getItem("nx-token");
  const response = await fetch(`/api${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok)
    throw new Error("Export failed. Check access and select a completed run.");
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const percent = (value: number | null | undefined) =>
  value == null ? "N/A" : `${(value * 100).toFixed(1)}%`;
export const short = (value: string | undefined) =>
  value ? value.slice(0, 8) : "—";
export const title = (value: string) =>
  value.replaceAll("_", " ").replace(/^./, (s) => s.toUpperCase());
