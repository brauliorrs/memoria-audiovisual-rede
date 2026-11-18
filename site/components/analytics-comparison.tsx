"use client";

import {useMemo,useState} from "react";
import Link from "next/link";
import {historicalAnalyticReports} from "@/lib/historical-analytics";
import {corpusList,formatNumber} from "@/lib/scientific-observatory";

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
 const [query,setQuery]=useState("");
 const [sort,setSort]=useState("institutions");
 const items=useMemo(()=>historicalAnalyticReports.filter(r=>[r.code,r.source].join(" ").toLowerCase().includes(query.trim().toLowerCase())).sort((a,b)=>sort==="video"?b.institutionsWithVideo-a.institutionsWithVideo:sort==="name"?a.code.localeCompare(b.code):b.totalInstitutions-a.totalInstitutions),[query,sort]);
 return <section>
  <div className="ob-filter-panel">
   <div><label htmlFor="analyses-search">Filtrar fontes</label><input id="analyses-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex.: APE, Eye, Europeana"/></div>
   <div><label htmlFor="analyses-sort">Ordenar por</label><select id="analyses-sort" value={sort} onChange={e=>setSort(e.target.value)}><option value="institutions">Instituições mapeadas</option><option value="video">Instituições com vídeo detectado</option><option value="name">Código da fonte</option></select></div>
  </div>
  <p className="access-result-count">{items.length} relatórios analíticos históricos</p>
  <div className="ob-table-scroll"><table className="ob-table"><thead><tr><th>Fonte e relatório</th><th>Instituições avaliadas*</th><th>Com sinal de vídeo*</th><th>Com incorporação detectada*</th><th>Perfil</th></tr></thead><tbody>{items.map(report=><tr key={report.code}>
    <td><strong>{report.code.toUpperCase().replaceAll("_"," ")}</strong><small>{report.source}</small></td>
    <td>{formatNumber(report.totalInstitutions)}</td>
    <td>{formatNumber(report.institutionsWithVideo)}</td>
    <td>{formatNumber(report.withEmbeds)}</td>
    <td><Link href={`/pesquisa/${report.code}/`}>Explorar dimensões</Link>{linkFor(report.code)&&<> · <Link href={linkFor(report.code)!}>Perfil</Link></>}</td>
   </tr>)}</tbody></table></div>
  <p className="disclaimer">* Relatórios gerados anteriormente no Streamlit e preservados como dados agregados; coberturas e denominadores variam por fonte, podendo existir instituições repetidas. <strong>Não somar as linhas como um total mundial de instituições ou obras.</strong> Indicadores de vídeo não constituem autorização para exibição de conteúdo.</p>
 </section>;
}
