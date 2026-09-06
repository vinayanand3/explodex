export function resolveAssetUrl(path: string): string {
  if (!path || /^https?:\/\//i.test(path) || /^blob:/i.test(path) || /^data:/i.test(path)) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  let base: string = import.meta.env.BASE_URL || '/';

  // Robust runtime detection for GitHub Pages sub-path hosting
  if (typeof window !== 'undefined' && (base === '/' || base === './')) {
    const parts = window.location.pathname.split('/').filter(Boolean);
    if (parts.length > 0 && (window.location.hostname.endsWith('github.io') || parts[0] === 'explodex')) {
      base = `/${parts[0]}/`;
    }
  }

  const cleanBase = base.endsWith('/') ? base : `${base}/`;
  return `${cleanBase}${cleanPath}`;
}
