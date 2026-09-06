export function resolveAssetUrl(path: string): string {
  if (!path || /^https?:\/\//i.test(path) || /^blob:/i.test(path) || /^data:/i.test(path)) {
    return path;
  }
  const meta = (typeof import.meta !== 'undefined' ? import.meta : {}) as unknown as { env?: { BASE_URL?: string } };
  const base = meta.env?.BASE_URL || '/';
  const cleanBase = base.endsWith('/') ? base : `${base}/`;
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${cleanBase}${cleanPath}`;
}
