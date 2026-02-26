import type { SearchResult } from "@/lib/types";

export function GoogleSearchResults({ items }: { items: SearchResult[] }) {
  return (
    <ol className="space-y-3">
      {items.map((item, i) => (
        <li key={i} className="border-l-2 border-muted-foreground/20 pl-3">
          <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:underline dark:text-blue-400"
          >
            {item.title}
          </a>
          <p className="text-xs text-muted-foreground truncate">{item.link}</p>
          <p className="text-sm">{item.snippet}</p>
        </li>
      ))}
    </ol>
  );
}
