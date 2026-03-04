import type { ProviderResult, ComparisonResult } from "./types";

export function exportAsJSON(
  query: string,
  results: ProviderResult[],
  comparison?: ComparisonResult | null,
  filename?: string,
) {
  const data: Record<string, unknown> = {
    query,
    exported_at: new Date().toISOString(),
    results,
  };
  if (comparison) {
    data.comparison = {
      summary: comparison.summary,
      claims: comparison.claims,
      provider_rankings: comparison.provider_rankings,
      model_used: comparison.model_used,
      generated_at: comparison.generated_at,
    };
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  downloadBlob(blob, filename ?? `query_export_${Date.now()}.json`);
}

export function exportAsCSV(
  query: string,
  results: ProviderResult[],
  comparison?: ComparisonResult | null,
  filename?: string,
) {
  const headers = ["Provider", "Model", "Success", "Response Time (s)", "Response Length", "Response"];
  const rows = results.map((r) => [
    r.provider,
    r.model ?? "",
    r.success ? "Yes" : "No",
    r.response_time?.toString() ?? "",
    r.response_length?.toString() ?? "",
    typeof r.response === "string" ? r.response.replace(/"/g, '""') : JSON.stringify(r.response ?? ""),
  ]);

  const csvParts = [
    `# Query: ${query.replace(/"/g, '""')}`,
    headers.map((h) => `"${h}"`).join(","),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
  ];

  if (comparison) {
    csvParts.push("");
    csvParts.push("# Cross-Provider Comparison");
    csvParts.push(`# Model: ${comparison.model_used}`);
    csvParts.push(`# Generated: ${comparison.generated_at}`);
    csvParts.push("");
    csvParts.push('"Comparison Summary"');
    csvParts.push(`"${comparison.summary.replace(/"/g, '""')}"`);

    if (comparison.claims?.length) {
      csvParts.push("");
      const claimProviders = Object.keys(comparison.provider_rankings);
      const claimHeaders = ["Claim", "Category", ...claimProviders.map((p) => `${p} Stance`), ...claimProviders.map((p) => `${p} Detail`)];
      csvParts.push(claimHeaders.map((h) => `"${h}"`).join(","));
      for (const claim of comparison.claims) {
        const row = [
          claim.claim.replace(/"/g, '""'),
          claim.category,
          ...claimProviders.map((p) => claim.providers[p] ?? ""),
          ...claimProviders.map((p) => (claim.details[p] ?? "").replace(/"/g, '""')),
        ];
        csvParts.push(row.map((cell) => `"${cell}"`).join(","));
      }
    }

    if (comparison.provider_rankings) {
      csvParts.push("");
      csvParts.push('"Provider Rankings"');
      csvParts.push('"Provider","Completeness","Accuracy Signals","Sourcing","Unique Value"');
      for (const [provider, ranking] of Object.entries(comparison.provider_rankings)) {
        csvParts.push(
          [
            provider,
            ranking.completeness.toString(),
            ranking.accuracy_signals.toString(),
            ranking.sourcing.toString(),
            ranking.unique_value.replace(/"/g, '""'),
          ]
            .map((cell) => `"${cell}"`)
            .join(","),
        );
      }
    }
  }

  const blob = new Blob([csvParts.join("\n")], { type: "text/csv" });
  downloadBlob(blob, filename ?? `query_export_${Date.now()}.csv`);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
