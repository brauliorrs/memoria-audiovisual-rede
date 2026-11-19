"use client";

import { useMemo, useState } from "react";
import inventory from "@/data/public-access-observatory.json";
import {useSiteLocale} from "@/components/site-locale";
import {useScientificCopy} from "@/components/scientific-i18n";

type Corpus = (typeof inventory.corpora)[number];
type Filter = "all" | "historically-public" | "restricted" | "unquantified";

function displayReason(corpus: Corpus, copy: {accessFallbackUnquantified:string;accessFallbackPublic:string}) {
  // Original source evidence is research data, not an editorial translation.
  if (corpus.restrictionEvidence) return corpus.restrictionEvidence;
  if (corpus.historicalTotal === 0) return copy.accessFallbackUnquantified;
  return copy.accessFallbackPublic;
}

export function PublicAccessInventory() {
  const copy=useScientificCopy();
  const {locale}=useSiteLocale();
  const fmt=(value:number)=>new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(value);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const results = useMemo(() => inventory.corpora.filter((item) => {
    const q = query.trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const searchable = [item.name, item.shortLabel, item.code, item.accessCategory ?? "", item.continent].join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    if (q && !searchable.includes(q)) return false;
    if (filter === "historically-public") return item.historicalPublicSurfaceRecords > 0;
    if (filter === "restricted") return item.historicalRestrictedRecords > 0;
    if (filter === "unquantified") return item.historicalTotal === 0;
    return true;
  }), [query, filter]);

  return <section aria-label={copy.accessSearchSection}>
    <div className="search-panel access-controls">
      <label htmlFor="access-search" className="search-label">{copy.accessSearchLabel}</label>
      <input id="access-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={copy.accessSearchPlaceholder} />
      <label className="filter-label" htmlFor="access-filter">{copy.accessStatusLabel}
        <select id="access-filter" value={filter} onChange={event => setFilter(event.target.value as Filter)}>
          <option value="all">{copy.accessAll}</option>
          <option value="historically-public">{copy.accessPublicHistory}</option>
          <option value="restricted">{copy.accessRestricted}</option>
          <option value="unquantified">{copy.accessUnquantified}</option>
        </select>
      </label>
    </div>
    <p className="access-result-count" role="status">{fmt(results.length)} {copy.accessResultsSuffix} · {copy.accessPublicationHold}</p>
    <div className="access-list">
      {results.map(item => <article className="access-entry" key={item.code}>
        <div className="access-entry-head"><div><p className="eyebrow">{item.continent === "Europe" ? copy.accessEurope : item.continent === "North America" ? copy.accessNorthAmerica : copy.accessUnclassified} · {item.code}</p><h2>{item.name}</h2></div>
        <span className="access-state">{item.historicalTotal === 0 ? copy.accessIdentifiedNoVolume : copy.accessIdentifiedNoFiches}</span></div>
        <p className="access-reason"><strong>{copy.accessReasonLead}</strong> {displayReason(item,copy)}</p>
        <p className="access-reason"><strong>{copy.accessVisitorLead}</strong> {item.humanAccessNote} {item.sampleSourceUrl && <a href={item.sampleSourceUrl} target="_blank" rel="noopener noreferrer">{copy.accessSourceLink}</a>} {item.rightsPolicyUrl && <a href={item.rightsPolicyUrl} target="_blank" rel="noopener noreferrer">{copy.accessPolicyLink}</a>}</p>
        <dl className="access-metrics">
          <div><dt>{copy.accessPublicRecords}</dt><dd>{fmt(item.historicalPublicSurfaceRecords)}</dd></div>
          <div><dt>{copy.accessRestrictedRecords}</dt><dd>{fmt(item.historicalRestrictedRecords)}</dd></div>
          <div><dt>{copy.accessNewFiches}</dt><dd>0</dd></div>
        </dl>
        {item.accessCategory && <p className="access-category">{copy.accessHistoricalClass} {item.accessCategory}</p>}
      </article>)}
    </div>
    {results.length === 0 && <p>{copy.accessNoMatches}</p>}
    <p className="disclaimer">* {copy.accessFootnoteBefore} {inventory.observedRuleVersion}{copy.accessFootnoteAfter} {copy.accessOriginalNote}</p>
  </section>;
}
