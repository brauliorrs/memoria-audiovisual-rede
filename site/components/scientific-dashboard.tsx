"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { accessSummary, corpusList, groupByCategory, groupByTerritory } from "@/lib/scientific-observatory";
import {useSiteLocale} from "@/components/site-locale";
import {useScientificCopy,localizeTerritory} from "@/components/scientific-i18n";

type View = "corpora" | "territory" | "category";
type Access = "all" | "public" | "restricted" | "without";

function Meter({ available, restricted }: { available: number; restricted: number }) {
  const copy=useScientificCopy();
  const {locale}=useSiteLocale();
  const fmt=(n:number)=>new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(n);
  const total = available + restricted;
  if (!total) return <span className="ob-meter-empty">{copy.obNoVolume}</span>;
  return <div className="ob-meter" role="img" aria-label={`${copy.obMeterPublic}: ${fmt(available)}; ${copy.obMeterRestricted}: ${fmt(restricted)}`}>
    <span className="ob-meter-public" style={{ width: `${100 * available / total}%` }} />
    <span className="ob-meter-restricted" style={{ width: `${100 * restricted / total}%` }} />
  </div>;
}

export function ScientificDashboard() {
  const copy=useScientificCopy();
  const {locale}=useSiteLocale();
  const fmt=(n:number)=>new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(n);
  const [view, setView] = useState<View>("corpora");
  const [access, setAccess] = useState<Access>("all");
  const [continent, setContinent] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("total");

  const filtered = useMemo(() => corpusList.filter(item => {
    if (continent !== "all" && item.continent !== continent) return false;
    if (access === "public" && item.historicalPublicSurfaceRecords <= 0) return false;
    if (access === "restricted" && item.historicalRestrictedRecords <= 0) return false;
    if (access === "without" && item.historicalTotal > 0) return false;
    const terms = [item.name, item.code, item.shortLabel, item.category, item.continent].filter(Boolean).join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const q = query.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
    return !q || terms.includes(q);
  }), [access, continent, query]);

  const totals = useMemo(() => accessSummary(filtered), [filtered]);
  const table = useMemo(() => [...filtered].sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name, "pt-BR");
    if (sort === "restricted") return b.historicalRestrictedRecords - a.historicalRestrictedRecords;
    if (sort === "public") return b.historicalPublicSurfaceRecords - a.historicalPublicSurfaceRecords;
    return b.historicalTotal - a.historicalTotal;
  }), [filtered, sort]);
  const categories = useMemo(() => groupByCategory(filtered), [filtered]);
  const territories = useMemo(() => groupByTerritory(filtered), [filtered]);

  return <div className="ob-dashboard">
    <section className="ob-filter-panel" aria-label={copy.obFilterGroup}>
      <div><label htmlFor="ob-query">{copy.obQuery}</label><input id="ob-query" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder={copy.obQueryHint} /></div>
      <div><label htmlFor="ob-continent">{copy.obTerritory}</label><select id="ob-continent" value={continent} onChange={e => setContinent(e.target.value)}><option value="all">{copy.obAll}</option><option value="Europe">{copy.obEurope}</option><option value="North America">{copy.obNorthAmerica}</option><option value="Nao classificado">{copy.obUnclassified}</option></select></div>
      <div><label htmlFor="ob-access">{copy.obAccess}</label><select id="ob-access" value={access} onChange={e => setAccess(e.target.value as Access)}><option value="all">Todos</option><option value="public">{copy.obPublicSurface}</option><option value="restricted">{copy.obRestricted}</option><option value="without">{copy.obWithout}</option></select></div>
    </section>
    <section className="ob-kpis" aria-label={copy.obKpiGroup}>
      <div><strong>{fmt(totals.units)}</strong><span>{copy.obUnits}</span></div>
      <div><strong>{fmt(totals.withRecords)}</strong><span>{copy.obWithRecords}</span></div>
      <div><strong>{fmt(totals.publicSurface)}</strong><span>{copy.obPublicCount}</span></div>
      <div><strong>{fmt(totals.restricted)}</strong><span>{copy.obRestrictedCount}</span></div>
    </section>
    <div className="ob-viewbar">
      <div className="ob-viewtabs" role="group" aria-label={copy.obViewGroup}>
        <button type="button" aria-pressed={view === "corpora"} onClick={() => setView("corpora")}>{copy.obCorpora}</button>
        <button type="button" aria-pressed={view === "territory"} onClick={() => setView("territory")}>{copy.obTerritories}</button>
        <button type="button" aria-pressed={view === "category"} onClick={() => setView("category")}>{copy.obCategories}</button>
      </div>
      {view === "corpora" && <label className="ob-sort" htmlFor="ob-sort">{copy.obSort} <select id="ob-sort" value={sort} onChange={e => setSort(e.target.value)}><option value="total">{copy.obSortTotal}</option><option value="public">{copy.obSortPublic}</option><option value="restricted">{copy.obSortRestricted}</option><option value="name">{copy.obSortName}</option></select></label>}
    </div>
    {view === "corpora" ? <div className="ob-table-scroll"><table className="ob-table"><thead><tr><th>{copy.obCorpusHeading}</th><th>{copy.obAccessDistribution}</th><th>{copy.obPublicShort}</th><th>{copy.obRestrictedShort}</th><th>{copy.obStudy}</th></tr></thead><tbody>{table.map(item => <tr key={item.code}><td><strong>{item.name}</strong><small>{item.shortLabel} · {item.category}</small></td><td><Meter available={item.historicalPublicSurfaceRecords} restricted={item.historicalRestrictedRecords}/></td><td>{fmt(item.historicalPublicSurfaceRecords)}</td><td>{fmt(item.historicalRestrictedRecords)}</td><td><Link href={`/observatorio/${item.code}/`}>{copy.obOpen}</Link></td></tr>)}</tbody></table></div>
      : <div className="ob-group-list">{(view === "territory" ? territories : categories).map(item => <article key={item.name} className="ob-group"><div><h2>{view === "territory"?localizeTerritory(item.name,locale):item.name}</h2><p>{fmt(item.count)} {copy.obUnits.toLowerCase()} · {fmt(item.publicSurface + item.restricted)} {copy.obRecords}</p></div><Meter available={item.publicSurface} restricted={item.restricted}/><p><strong>{fmt(item.publicSurface)}</strong> {copy.obSurfacePhrase} · <strong>{fmt(item.restricted)}</strong> {copy.obRestrictedPhrase}</p></article>)}</div>}
    <p className="disclaimer" role="note">* {copy.obDisclaimer} <Link href="/acervo/">{copy.obCatalog}</Link>.</p>
  </div>;
}
