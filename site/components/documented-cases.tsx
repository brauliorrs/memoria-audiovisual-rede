"use client";

import {useMemo,useState} from "react";
import cases from "@/data/documented-cases.json";
import {useScientificCopy} from "@/components/scientific-i18n";
import {useSiteLocale} from "@/components/site-locale";
export function DocumentedCases() {
 const copy=useScientificCopy();
 const {locale}=useSiteLocale();
 const [query,setQuery]=useState("");
 const [expanded,setExpanded]=useState<string|null>(null);
 const filtered=useMemo(()=>cases.cases.filter(item=>[item.name,item.scope,item.category,item.reason].join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().includes(query.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim())),[query]);
 return <section aria-label={copy.casesTitle}>
  <div className="ob-filter-panel"><div><label htmlFor="case-search">{copy.casesFilter}</label><input id="case-search" placeholder={copy.casesHint} value={query} onChange={e=>setQuery(e.target.value)}/></div></div>
  <p className="access-result-count">{new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(filtered.length)} {copy.casesCount}</p>
  <div className="ob-group-list">{filtered.map(item=><article className="ob-panel" key={item.code}>
   <p className="eyebrow">{item.scope} · {item.code}</p>
   <h2>{item.name}</h2><p><strong>{copy.casesCondition}:</strong> {item.category.replaceAll("_"," ")}</p>
   <p>{item.reason}</p>
   <button type="button" className="ob-case-toggle" onClick={()=>setExpanded(expanded===item.code?null:item.code)} aria-expanded={expanded===item.code}>{expanded===item.code?copy.casesHide:copy.casesExpand}</button>
   {expanded===item.code&&<div className="ob-case-detail"><h3>{copy.casesRationale}</h3><p>{item.evidence}</p><h3>{copy.casesNext}</h3><p>{item.nextStep}</p><p><strong>{copy.casesProtocol}:</strong> {item.protocol}</p></div>}
  </article>)}</div>
  <p className="disclaimer">{copy.casesWarning}</p>
 </section>;
}
