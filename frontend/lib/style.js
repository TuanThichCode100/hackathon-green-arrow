// Converts an inline-CSS string ("padding:12px; color:#fff") into a React style
// object. Lets us reuse the exact style strings from the original prototype.
export function s(css) {
  const out = {};
  if (!css) return out;
  css.split(';').forEach((decl) => {
    const i = decl.indexOf(':');
    if (i < 0) return;
    const key = decl.slice(0, i).trim();
    const val = decl.slice(i + 1).trim();
    if (!key) return;
    const camel = key.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    out[camel] = val;
  });
  return out;
}
