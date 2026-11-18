"use client";

import Link from "next/link";
import {useSiteLocale} from "@/components/site-locale";
import {useScientificCopy} from "@/components/scientific-i18n";
import { type HistoricalAnalyticReport, rankSummary } from "@/lib/historical-analytics";

function useFormat(){
  const {locale}=useSiteLocale();
  const region=locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US";
  return (value:number)=>new Intl.NumberFormat(region).format(value);
}
function Distribution({title, values}: {title:string, values:Record<string,number>}) {
  const formatNumber=useFormat();
  const entries=rankSummary(values,10);
  if (!entries.length) return null;
  const max=Math.max(...entries.map(([,number])=>number),1);
  return <div className="ob-panel">
    <h3>{title}</h3>
    <div className="ob-bars">{entries.map(([label,value])=><div className="ob-bar-item" key={label}>
      <div className="ob-bar-label"><span>{label.replaceAll("_"," ")}</span><strong>{formatNumber(value)}</strong></div>
      <div className="ob-bar-track" role="img" aria-label={label+": "+formatNumber(value)}><span style={{width:`${100*value/max}%`}}/></div>
    </div>)}</div>
  </div>;
}

export function CorpusHistoricalAnalytics({report}:{report:HistoricalAnalyticReport}) {
  const copy=useScientificCopy();
  const formatNumber=useFormat();
  return <section className="ob-analytic-section" aria-label={copy.corSection}>
    <p className="eyebrow">{copy.corEyebrow}</p>
    <h2>{copy.corTitle}</h2>
    <p>{copy.corIntro}</p>
    <div className="ob-kpis">
      <div><strong>{formatNumber(report.totalInstitutions)}</strong><span>{copy.corInstitutions}</span></div>
      <div><strong>{formatNumber(report.institutionsWithVideo)}</strong><span>{copy.corWithVideo}</span></div>
      <div><strong>{formatNumber(report.withEmbeds)}</strong><span>{copy.corWithEmbeds}</span></div>
      <div><strong>{formatNumber(Object.values(report.platforms).reduce((a,b)=>a+b,0))}</strong><span>{copy.corPlatformOccurrences}</span></div>
    </div>
    <div className="ob-group-list">
      <Distribution title={copy.corSites} values={report.siteStatus}/>
      <Distribution title={copy.corIntegrity} values={report.integrity}/>
      <Distribution title={copy.corPlatforms} values={report.platforms}/>
      <Distribution title={copy.corContinents} values={report.continents}/>
    </div>
    <p className="disclaimer">* {copy.corDisclaimer} <code>{report.source}</code></p>
    <p><Link href={`/pesquisa/${report.code}/`}>{copy.corExplore}</Link></p>
    <p><Link href="/analises/">{copy.corCompare}</Link></p>
  </section>;
}
