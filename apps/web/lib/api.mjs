// Plain-JS mirror of lib/api.ts so the Node test runner can exercise the
// URL-joining logic without a TypeScript toolchain.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function apiUrl(path) {
  const base = API_BASE_URL.replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}
