import type { ProviderResult } from "./types";

export function exportAsJSON(query: string, results: ProviderResult[], filename?: string) {
  const data = {
    query,
    exported_at: new Date().toISOString(),
    results,
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  downloadBlob(blob, filename ?? `query_export_${Date.now()}.json`);
}

export function exportAsCSV(query: string, results: ProviderResult[], filename?: string) {
  const headers = ["Provider", "Model", "Success", "Response Time (s)", "Response Length", "Response"];
  const rows = results.map((r) => [
    r.provider,
    r.model ?? "",
    r.success ? "Yes" : "No",
    r.response_time?.toString() ?? "",
    r.response_length?.toString() ?? "",
    typeof r.response === "string" ? r.response.replace(/"/g, '""') : JSON.stringify(r.response ?? ""),
  ]);

  const csv = [
    `# Query: ${query.replace(/"/g, '""')}`,
    headers.map((h) => `"${h}"`).join(","),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
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
