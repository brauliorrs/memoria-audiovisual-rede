/** Versioned, allowlisted URL representation of a MAR scientific research slice.
 * Client-only URL state, never a database query or a permission to publish items.
 */
import {comparisonMetrics, comparisonSources, type ComparisonDimension, type ComparisonMetric} from "@/lib/corpus-comparison";

export type ComparisonView = "distributions" | "timeline";
export type ResearchLanguage = "pt" | "en" | "es";

export interface ResearchSliceState {
  sources: [string, string, string];
  view: ComparisonView;
  dimension: ComparisonDimension;
  metric: ComparisonMetric;
  query: string;
  sharedOnly: boolean;
  locale: ResearchLanguage;
}

const dimensions: readonly ComparisonDimension[] = ["theme", "country", "platform"];
const views: readonly ComparisonView[] = ["distributions", "timeline"];
const langs: readonly ResearchLanguage[] = ["pt", "en", "es"];
const MAX_QUERY = 96;

const initialA = comparisonSources.includes("ape") ? "ape" : comparisonSources[0] ?? "";
const initialB = comparisonSources.includes("eye") ? "eye" : comparisonSources.find(c => c !== initialA) ?? "";
const initialC = comparisonSources.includes("europeana") ? "europeana" : "";

export const defaultSliceState: ResearchSliceState = {
  sources: [initialA, initialB, initialC],
  view: "distributions",
  dimension: "theme",
  metric: "video_links_total",
  query: "",
  sharedOnly: false,
  locale: "pt",
};

function isMember<T extends string>(value: string | null, collection: readonly T[]): value is T {
  return value !== null && (collection as readonly string[]).includes(value);
}

function cleanSources(params: URLSearchParams): [string, string, string] {
  const candidates = [params.get("a"), params.get("b"), params.get("c")];
  if (!candidates.some(Boolean)) return [...defaultSliceState.sources];
  const chosen: string[] = [];
  for (const candidate of candidates) {
    if (candidate && comparisonSources.includes(candidate) && !chosen.includes(candidate)) chosen.push(candidate);
  }
  // Never let malformed URLs bypass the minimum-two-corpi comparison contract.
  for (const fallback of comparisonSources) {
    if (chosen.length >= 2) break;
    if (!chosen.includes(fallback)) chosen.push(fallback);
  }
  return [chosen[0] ?? initialA, chosen[1] ?? initialB, chosen[2] ?? ""];
}

/** Invalid/unrecognized values are ignored; no corpus paths or arbitrary SQL can enter state. */
export function decodeResearchSlice(params: URLSearchParams): ResearchSliceState {
  const view = params.get("view");
  const dimension = params.get("dimension");
  const metric = params.get("metric");
  const lang = params.get("lang");
  return {
    sources: cleanSources(params),
    view: isMember(view, views) ? view : defaultSliceState.view,
    dimension: isMember(dimension, dimensions) ? dimension : defaultSliceState.dimension,
    metric: isMember(metric, comparisonMetrics) ? metric : defaultSliceState.metric,
    query: (params.get("q") ?? "").replace(/[\u0000-\u001f\u007f]/g, "").slice(0, MAX_QUERY),
    sharedOnly: params.get("shared") === "1",
    locale: isMember(lang, langs) ? lang : defaultSliceState.locale,
  };
}

/** Deterministic parameter order; same scientific slice always generates same URL. */
export function encodeResearchSlice(slice: ResearchSliceState): URLSearchParams {
  const params = new URLSearchParams();
  const selected = [...new Set(slice.sources)].filter(s => comparisonSources.includes(s)).slice(0, 3);
  if (selected[0]) params.set("a", selected[0]);
  if (selected[1]) params.set("b", selected[1]);
  if (selected[2]) params.set("c", selected[2]);
  params.set("view", slice.view);
  params.set("dimension", slice.dimension);
  params.set("metric", slice.metric);
  const query = slice.query.replace(/[\u0000-\u001f\u007f]/g, "").slice(0, MAX_QUERY);
  if (query) params.set("q", query);
  if (slice.sharedOnly) params.set("shared", "1");
  params.set("lang", slice.locale);
  return params;
}
