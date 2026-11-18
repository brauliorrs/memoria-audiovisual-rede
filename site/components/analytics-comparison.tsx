"use client";

import {useMemo,useState} from "react";
import Link from "next/link";
import {historicalAnalyticReports} from "@/lib/historical-analytics";
import {corpusList} from "@/lib/scientific-observatory";
import {useSiteLocale} from "@/components/site-locale";
import {useScientificCopy} from "@/components/scientific-i18n";

const corpusCodeByReport:Record<string,string>={
 "czech_tv":"czech-television","efa_estonia":"estonian_film_archive",
 "cinemateca_pt":"cinemateca-portuguesa","efg":"european-film-gateway",
 "home_movies":"home-movies-memoryscapes","csc_cineteca":"csc-cineteca-nazionale",
 "ppa":"portal-portugues-arquivos","filmoteca_vasca":"filmoteca-vasca"
};
function linkFor(code:string) {
 const candidate=corpusCodeByReport[code]??code.replaceAll("_","-");
 if(corpusList.some(c=>c.code===candidate))return `/observatorio/${candidate}/`;
 const found=corpusList.find(c=>c.code===code);
 return found?`/observatorio/${found.code}/`:null;
}

export function AnalyticsComparison() {
 const copy=useScientificCopy();
 const {locale}=useSiteLocale();
 const fmt=(n:number)=>new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(n);
 const [query,setQuery]=useState("");
 const [sort,setSort]=useState("institutions");
 const items=useMemo(()=>historicalAnalyticReports.filter(r=>[r.code,r.source].join(" ").toLowerCase().includes(query.trim().toLowerCase())).sort((a,b)=>sort==="video"?b.institutionsWithVideo-a.institutionsWithVideo:sort==="name"?a.code.localeCompare(b.code):b.totalInstitutions-a.totalInstitutions),[query,sort]);
 return <section>
  <div className="ob-filter-panel">
   <div><label htmlFor="analyses-search">{copy.anFilter}</label><input id="analyses-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder={copy.anFilterHint}/></div>
   <div><label htmlFor="analyses-sort">{copy.anSort}</label><select id="analyses-sort" value={sort} onChange={e=>setSort(e.target.value)}><option value="institutions">{copy.anSortInstitutions}</option><option value="video">{copy.anSortWithVideo}</option><option value="name">{copy.anSortCode}</option></select></div>
  </div>
  <p className="access-result-count">{fmt(items.length)} {copy.anReports}</p>
  <div className="ob-table-scroll"><table className="ob-table"><thead><tr><th>{copy.anSourceReport}</th><th>{copy.anInstitutionsReviewed}</th><th>{copy.anVideoSignal}</th><th>{copy.anEmbedSignal}</th><th>{copy.anProfile}</th></tr></thead><tbody>{items.map(report=><tr key={report.code}>
    <td><strong>{report.code.toUpperCase().replaceAll("_"," ")}</strong><small>{report.source}</small></td>
    <td>{fmt(report.totalInstitutions)}</td>
    <td>{fmt(report.institutionsWithVideo)}</td>
    <td>{fmt(report.withEmbeds)}</td>
    <td><Link href={`/pesquisa/${report.code}/`}>{copy.anExploreDimensions}</Link>{linkFor(report.code)&&<> · <Link href={linkFor(report.code)!}>{copy.anProfile}</Link></>}</td>
   </tr>)}</tbody></table></div>
  <p className="disclaimer">* {copy.anDisclaimer} <strong>{copy.anNoSum}</strong> {copy.anMediaWarning}</p>
 </section>;
}
