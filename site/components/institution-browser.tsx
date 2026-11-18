"use client";
import {useMemo,useState} from "react";
import Link from "next/link";
import {useSiteLocale} from "@/components/site-locale";
import {institutionalProfiles,institutionSources,institutionGroups} from "@/lib/institutional-profiles";

export function InstitutionBrowser(){
 const {t,locale}=useSiteLocale();
 const [query,setQuery]=useState("");
 const [source,setSource]=useState("all");
 const [country,setCountry]=useState("all");
 const [page,setPage]=useState(1);
 const countryOptions=useMemo(()=>[...new Set(institutionalProfiles.map(x=>x.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b)),[]);
 const filtered=useMemo(()=>{const q=query.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim();return institutionalProfiles.filter(x=>(source==="all"||x.source===source)&&(country==="all"||x.country===country)&&(!q||[x.name,x.country,x.type,x.repositoryCode,x.source].join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().includes(q))).sort((a,b)=>a.name.localeCompare(b.name,locale==="pt"?"pt-BR":locale))},[query,source,country,locale]);
 const size=24,maxPages=Math.max(1,Math.ceil(filtered.length/size));
 const actualPage=Math.min(page,maxPages);
 const rows=filtered.slice((actualPage-1)*size,actualPage*size);
 const selectedIsSampled=source!=="all"&&institutionGroups[source]?.sampled;
 const update=(fn:()=>void)=>{fn();setPage(1)};
 return <section className="institution-browser">
 <div className="ob-filter-panel">
  <div><label htmlFor="inst-search">{t("filter")}</label><input id="inst-search" value={query} onChange={e=>update(()=>setQuery(e.target.value))} placeholder={t("filter")}/></div>
  <div><label htmlFor="inst-source">{t("source")}</label><select id="inst-source" value={source} onChange={e=>update(()=>setSource(e.target.value))}><option value="all">{t("all")}</option>{institutionSources.map(code=><option key={code} value={code}>{code.replaceAll("_"," ").toUpperCase()}</option>)}</select></div>
  <div><label htmlFor="inst-country">{t("country")}</label><select id="inst-country" value={country} onChange={e=>update(()=>setCountry(e.target.value))}><option value="all">{t("all")}</option>{countryOptions.map(c=><option key={c} value={c}>{c}</option>)}</select></div>
 </div>
 <div className="ob-kpis"><div><strong>{filtered.length.toLocaleString(locale==="pt"?"pt-BR":locale)}</strong><span>{t("totalInstitutions")}</span></div><div><strong>{institutionSources.length}</strong><span>{t("sourceProfiles")}</span></div></div>
 {selectedIsSampled&&<p className="disclaimer">{t("coverage")}: subset. {t("historicalWarning")}</p>}
 <div className="institution-research-grid">
 {rows.map(item=><article className="ob-panel" key={item.id}>
  <p className="eyebrow">{item.source.toUpperCase()} · {item.country||"—"}</p><h2>{item.name}</h2>
  <p>{item.type||"—"}</p>{item.repositoryCode&&<p><strong>ID:</strong> {item.repositoryCode}</p>}
  <Link href={`/instituicoes/pesquisa/${item.source}/${item.id.split(":")[1]}/`}>{t("study")}</Link>
 </article>)}
 </div>
 {!rows.length&&<p className="ob-panel">{t("noData")}</p>}
 <nav className="institution-pagination" aria-label="Pagination">
  <button type="button" disabled={actualPage===1} onClick={()=>setPage(actualPage-1)}>←</button>
  <span>{actualPage} / {maxPages}</span>
  <button type="button" disabled={actualPage===maxPages} onClick={()=>setPage(actualPage+1)}>→</button>
 </nav>
 <p className="disclaimer">{t("historicalWarning")} {t("sourceNote")}</p>
 </section>;
}
