/**
 * Return the URL only if it is an http(s) link, so data from the API can never
 * become a javascript: (or other scheme) link in the UI.
 */
export function safeExternalUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  try {
    const { protocol } = new URL(url);
    return protocol === 'http:' || protocol === 'https:' ? url : undefined;
  } catch {
    return undefined;
  }
}
