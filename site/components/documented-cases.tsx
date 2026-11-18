"use client";

import {useMemo,useState} from "react";
import cases from "@/data/documented-cases.json";
export function DocumentedCases() {
 const [query,setQuery]=useState("");
 const [expanded,setExpanded]=useState<string|null>(null);
 const filtered=useMemo(()=>cases.cases.filter(item=>[item.name,item.scope,item.category,item.reason].join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().includes(query.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim())),[query]);
 return <section aria-label="Casos documentados">
  <div className="ob-filter-panel"><div><label htmlFor="case-search">Pesquisar casos e instituições</label><input id="case-search" placeholder="Instituição, país, condição de acesso" value={query} onChange={e=>setQuery(e.target.value)}/></div></div>
  <p className="access-result-count">{filtered.length} casos documentados</p>
  <div className="ob-group-list">{filtered.map(item=><article className="ob-panel" key={item.code}>
   <p className="eyebrow">{item.scope} · {item.code}</p>
   <h2>{item.name}</h2><p><strong>Condição identificada:</strong> {item.category.replaceAll("_"," ")}</p>
   <p>{item.reason}</p>
   <button type="button" className="ob-case-toggle" onClick={()=>setExpanded(expanded===item.code?null:item.code)} aria-expanded={expanded===item.code}>{expanded===item.code?"Ocultar evidências":"Examinar fundamentação e próximos passos"}</button>
   {expanded===item.code&&<div className="ob-case-detail"><h3>Justificativa metodológica</h3><p>{item.evidence}</p><h3>Próxima investigação</h3><p>{item.nextStep}</p><p><strong>Protocolo:</strong> {item.protocol}</p></div>}
  </article>)}</div>
  <p className="disclaimer">Os casos descrevem limites de observação no levantamento histórico. Não presumem inexistência do patrimônio audiovisual nem autorização de reutilização de mídias. Fontes podem ter mudado desde o snapshot.</p>
 </section>;
}
