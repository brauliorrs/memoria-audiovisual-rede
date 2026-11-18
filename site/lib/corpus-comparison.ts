/** Historical multi-corpus comparisons. No original item metadata is imported. */
import {
  chronologicalObservations,
  getResearchSlice,
  researchSourceCodes,
  summarizeTopics,
  verifiedCount,
  type Observation,
} from "@/lib/research-slices";

export type ComparisonDimension = "theme" | "country" | "platform";
export type ComparisonMetric = "video_links_total" | "institutions" | "institutions_with_video_links" | "videos_in_curatorial_catalog" | "countries_with_videos";

export const comparisonSources = researchSourceCodes;
export const comparisonMetrics: ComparisonMetric[] = [
  "video_links_total",
  "institutions",
  "institutions_with_video_links",
  "videos_in_curatorial_catalog",
  "countries_with_videos",
];

/** Denominators are source-specific; never add sources into a global total. */
export interface SourceDistribution {
  code: string;
  sourcePath: string;
  counts: Record<string, number>;
  total: number;
  labels: number;
  available: boolean;
}

export interface ComparisonEntry {
  label: string;
  bySource: Record<string, { count: number; share: number } | null>;
  presentIn: number;
  maxShare: number;
}

export function sourceDistribution(code: string, dimension: ComparisonDimension): SourceDistribution {
  const slice = getResearchSlice(code);
  if (!slice) return {code, sourcePath: "", counts: {}, total: 0, labels: 0, available: false};
  const report = dimension === "theme" ? slice.tema_plataforma :
    dimension === "country" ? slice.tema_pais : slice.tema_plataforma;
  const rows = dimension === "theme"
    ? summarizeTopics(slice).map(r => ({name: r.name, count: r.total}))
    : dimension === "country"
      ? slice.tema_pais.rows.map(r => ({name: r.pais, count: verifiedCount(r.total)}))
      : slice.tema_plataforma.rows.map(r => ({name: r.plataforma, count: verifiedCount(r.total)}));

  const counts: Record<string, number> = {};
  for (const row of rows) {
    const name = row.name.trim();
    if (!name || !Number.isSafeInteger(row.count) || row.count < 0) continue;
    counts[name] = (counts[name] ?? 0) + row.count;
  }
  const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
  return {
    code, sourcePath: report.source, counts, total,
    labels: Object.keys(counts).length,
    available: rows.length > 0 && total > 0,
  };
}

export function compareDimensions(codes: string[], dimension: ComparisonDimension): {
  distributions: SourceDistribution[];
  entries: ComparisonEntry[];
} {
  const unique = [...new Set(codes)].filter(code => comparisonSources.includes(code)).slice(0, 3);
  const distributions = unique.map(code => sourceDistribution(code, dimension));
  const labels = new Set(distributions.flatMap(source => Object.keys(source.counts)));
  const entries = [...labels].map(label => {
    const bySource: ComparisonEntry["bySource"] = {};
    let presentIn = 0;
    let maxShare = 0;
    for (const source of distributions) {
      // null means the source has no observations for this label, not an invented zero.
      const count = source.counts[label];
      const share = source.total > 0 && count !== undefined ? count / source.total : 0;
      bySource[source.code] = count === undefined ? null : {count, share};
      if (count !== undefined && count > 0) presentIn++;
      maxShare = Math.max(maxShare, share);
    }
    return {label, bySource, presentIn, maxShare};
  }).sort((a, b) => b.presentIn - a.presentIn || b.maxShare - a.maxShare || a.label.localeCompare(b.label));
  return {distributions, entries};
}

export interface HistoricalSeries {
  code: string;
  sourcePath: string;
  points: {key: string; date: string; value: number}[];
}

export function historicalSeries(code: string, metric: ComparisonMetric): HistoricalSeries {
  const slice = getResearchSlice(code);
  if (!slice) return {code, sourcePath: "", points: []};
  const points = chronologicalObservations(slice).map((row: Observation) => ({
    key: row.observation_key,
    date: row.snapshot_generated_at,
    value: verifiedCount(row[metric]),
  }));
  return {code, sourcePath: slice.linha_do_tempo_corpus.source, points};
}

/** CSV output only contains public aggregate statistics; protect spreadsheet readers. */
export function csvCell(value: string | number | null | undefined): string {
  const raw = String(value ?? "");
  const protectedText = /^[\s]*[=+@\-]/.test(raw) ? "'" + raw : raw;
  return '"' + protectedText.replaceAll('"', '""') + '"';
}
export function toCsv(rows: (string | number | null | undefined)[][]): string {
  return "\ufeff" + rows.map(row => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
}
