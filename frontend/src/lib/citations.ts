export interface Source {
  index: number;
  url: string;
  title?: string;
  domain: string;
}

export interface CitationResult {
  sources: Source[];
}

const URL_REGEX = /https?:\/\/[^\s\])>"'`]+/g;
const MARKDOWN_LINK_REGEX = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;

function extractDomain(url: string): string {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/**
 * Extract unique sources (URLs) from response text.
 * Returns a deduplicated list of sources with titles when available.
 */
export function extractCitations(text: string): CitationResult {
  if (!text) return { sources: [] };

  const seen = new Map<string, Source>();
  let index = 1;

  // First pass: markdown links (these have titles)
  let match: RegExpExecArray | null;
  const mdRegex = new RegExp(MARKDOWN_LINK_REGEX.source, "g");
  while ((match = mdRegex.exec(text)) !== null) {
    const title = match[1];
    const url = cleanUrl(match[2]);
    if (!seen.has(url)) {
      seen.set(url, { index: index++, url, title, domain: extractDomain(url) });
    }
  }

  // Second pass: bare URLs not already captured
  const urlRegex = new RegExp(URL_REGEX.source, "g");
  while ((match = urlRegex.exec(text)) !== null) {
    const url = cleanUrl(match[0]);
    if (!seen.has(url)) {
      seen.set(url, { index: index++, url, domain: extractDomain(url) });
    }
  }

  return { sources: [...seen.values()] };
}

function cleanUrl(url: string): string {
  // Strip trailing punctuation that's likely not part of the URL
  return url.replace(/[.,;:!?)]+$/, "");
}
