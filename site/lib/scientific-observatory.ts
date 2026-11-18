import inventory from "@/data/public-access-observatory.json";

export type HistoricalCorpus = (typeof inventory.corpora)[number];

export const historicalSnapshot = inventory;
export const corpusList = inventory.corpora;
export const formatNumber = (value: number) => new Intl.NumberFormat("pt-BR").format(value);

export function getHistoricalCorpus(code: string): HistoricalCorpus | undefined {
  return corpusList.find((entry) => entry.code === code);
}

export function groupByCategory(items: readonly HistoricalCorpus[]) {
  const result = new Map<string, { count: number; publicSurface: number; restricted: number }>();
  for (const item of items) {
    const entry = result.get(item.category) ?? { count: 0, publicSurface: 0, restricted: 0 };
    entry.count += 1;
    entry.publicSurface += item.historicalPublicSurfaceRecords;
    entry.restricted += item.historicalRestrictedRecords;
    result.set(item.category, entry);
  }
  return [...result].map(([name, values]) => ({ name, ...values })).sort((a, b) => b.publicSurface + b.restricted - a.publicSurface - a.restricted);
}

export function groupByTerritory(items: readonly HistoricalCorpus[]) {
  const territory = new Map<string, { count: number; publicSurface: number; restricted: number }>();
  for (const item of items) {
    const name = item.continent === "Europe" ? "Europa" : item.continent === "North America" ? "América do Norte" : "Não classificado";
    const value = territory.get(name) ?? { count: 0, publicSurface: 0, restricted: 0 };
    value.count++;
    value.publicSurface += item.historicalPublicSurfaceRecords;
    value.restricted += item.historicalRestrictedRecords;
    territory.set(name, value);
  }
  return [...territory].map(([name, values]) => ({ name, ...values })).sort((a, b) => b.publicSurface + b.restricted - a.publicSurface - a.restricted);
}

export function accessSummary(items: readonly HistoricalCorpus[]) {
  return items.reduce((summary, corpus) => ({
    publicSurface: summary.publicSurface + corpus.historicalPublicSurfaceRecords,
    restricted: summary.restricted + corpus.historicalRestrictedRecords,
    units: summary.units + 1,
    withRecords: summary.withRecords + (corpus.historicalTotal > 0 ? 1 : 0),
  }), { publicSurface: 0, restricted: 0, units: 0, withRecords: 0 });
}
