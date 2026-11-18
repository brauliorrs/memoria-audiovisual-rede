"use client";

import Link from "next/link";
import {useMemo,useState} from "react";
import {useSiteLocale} from "@/components/site-locale";
import {getResearchSlice,researchSourceCodes,chronologicalObservations,summarizeTopics,verifiedCount,type TopicCountry,type TopicPlatform,type Observation} from "@/lib/research-slices";

type Metric="video_links_total"|"institutions"|"institutions_with_video_links"|"videos_in_curatorial_catalog"|"countries_with_videos";
const metricLabels:Record<Metric,"videoLinks"|"institutions"|"institutionsWithVideo"|"thematicCatalog"|"countries">={
 video_links_total:"videoLinks",institutions:"institutions",institutions_with_video_links:"institutionsWithVideo",
 videos_in_curatorial_catalog:"thematicCatalog",countries_with_videos:"countries"
};
function Distribution({title,items,n}:{title:string;items:{name:string;count:number}[];n:(v:number)=>string}){
 const max=Math.max(1,...items.map(x=>x.count));
 return <article className="ob-panel"><h3>{title}</h3>{items.length? <div className="ob-bars">{items.slice(0,16).map(item=><div key={item.name} className="ob-bar-item"><div className="ob-bar-label"><span>{item.name||"—"}</span><strong>{n(item.count)}</strong></div><div className="ob-bar-track" role="img" aria-label={`${item.name}: ${n(item.count)}`}><span style={{width:`${100*item.count/max}%`}}/></div></div>)}</div>:<p>—</p>}</article>;
}
function group<T>(rows:T[],filter:(v:T)=>boolean,name:(v:T)=>string,count:(v:T)=>number){
 const m=new Map<string,number>();
 for(const row of rows){if(filter(row)){const label=name(row);m.set(label,(m.get(label)||0)+count(row));}}
 return [...m].map(([name,count])=>({name,count})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
}
function SeriesChart({rows,metric,formatDate,format}:{rows:Observation[];metric:Metric;formatDate:(s:string)=>string;format:(n:number)=>string}){
 const points=rows.map(r=>verifiedCount(r[metric]));
 if(points.length<2)return null;
 const max=Math.max(...points,1),min=Math.min(...points);
 const range=Math.max(1,max-min);
 const d=points.map((v,i)=>`${32+(i/(points.length-1))*712},${215-((v-min)/range)*170}`).join(" ");
 return <figure className="research-series">
  <svg viewBox="0 0 780 260" role="img" aria-label={`Observed values: ${rows.map((r,i)=>`${formatDate(r.snapshot_generated_at)}: ${format(points[i])}`).join(", ")}`}>
   <path d="M32 215 H744" stroke="currentColor" strokeOpacity=".3" fill="none"/>
   <polyline points={d} fill="none" stroke="#0b6254" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
   {points.map((p,i)=><circle key={rows[i].observation_key||i} cx={32+(i/(points.length-1))*712} cy={215-((p-min)/range)*170} r={4} fill="#0b6254"/>)}
   <text x="30" y="25" fontSize="13" fill="currentColor">{format(max)}</text>
   <text x="30" y="240" fontSize="13" fill="currentColor">{format(min)}</text>
  </svg>
  <figcaption>{formatDate(rows[0].snapshot_generated_at)} — {formatDate(rows[rows.length-1].snapshot_generated_at)}</figcaption>
 </figure>;
}

export function ResearchWorkbench({mode,initialCorpus}:{mode:"themes"|"timeline";initialCorpus?:string}){
 const {t,locale}=useSiteLocale();
 const [source,setSource]=useState(initialCorpus&&getResearchSlice(initialCorpus)?initialCorpus:(mode==="timeline"?"eye":"ape"));
 const [theme,setTheme]=useState("");
 const [metric,setMetric]=useState<Metric>("video_links_total");
 const slice=getResearchSlice(source);
 const format=(n:number)=>new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(n);
 const formatDate=(s:string)=>new Intl.DateTimeFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-GB",{year:"numeric",month:"short",day:"numeric",timeZone:"UTC"}).format(new Date(s));
 const topics=useMemo(()=>slice?summarizeTopics(slice):[],[slice]);
 const activeTheme=topics.some(x=>x.name===theme)?theme:"";
 const countries=useMemo(()=>slice?group<TopicCountry>(slice.tema_pais.rows,r=>!activeTheme||r.tema===activeTheme,r=>r.pais,r=>verifiedCount(r.total)):[],[slice,activeTheme]);
 const platforms=useMemo(()=>slice?group<TopicPlatform>(slice.tema_plataforma.rows,r=>!activeTheme||r.tema===activeTheme,r=>r.plataforma,r=>verifiedCount(r.total)):[],[slice,activeTheme]);
 const dates=useMemo(()=>slice?chronologicalObservations(slice):[],[slice]);
 const totalCountries=countries.reduce((n,r)=>n+r.count,0);
 const totalPlatforms=platforms.reduce((n,r)=>n+r.count,0);
 return <section className="research-workbench">
  <div className="ob-filter-panel">
   <div><label htmlFor="research-source">{t("source")}</label><select id="research-source" value={source} onChange={e=>{setSource(e.target.value);setTheme("")}}>{researchSourceCodes.map(c=><option key={c} value={c}>{c.replaceAll("_"," ").toUpperCase()}</option>)}</select></div>
   {mode==="themes"&&<div><label htmlFor="research-topic">{t("theme")}</label><select id="research-topic" value={activeTheme} onChange={e=>setTheme(e.target.value)}><option value="">{t("all")}</option>{topics.map(o=><option key={o.name} value={o.name}>{o.name}</option>)}</select></div>}
   {mode==="timeline"&&<div><label htmlFor="research-metric">{t("metric")}</label><select id="research-metric" value={metric} onChange={e=>setMetric(e.target.value as Metric)}>{(Object.keys(metricLabels) as Metric[]).map(key=><option key={key} value={key}>{t(metricLabels[key])}</option>)}</select></div>}
  </div>
  {mode==="themes"?<>
   <div className="ob-kpis"><div><strong>{format(topics.length)}</strong><span>{t("topic")}</span></div><div><strong>{format(totalCountries)}</strong><span>{t("records")} · {t("country")}</span></div><div><strong>{format(totalPlatforms)}</strong><span>{t("records")} · {t("platform")}</span></div></div>
   {!topics.length?<p className="ob-panel">{t("noData")}</p>:<div className="ob-group-list"><Distribution title={t("country")} items={countries} n={format}/><Distribution title={t("platform")} items={platforms} n={format}/></div>}
   <p className="disclaimer">{t("independentFacets")}</p>
   <p className="disclaimer">{t("historicalWarning")}</p>
  </>:<>
   <div className="ob-kpis"><div><strong>{format(dates.length)}</strong><span>{t("observations")}</span></div><div><strong>{dates.length?format(verifiedCount(dates[dates.length-1][metric])):"—"}</strong><span>{t("value")} · {t(metricLabels[metric])}</span></div><div><strong>{dates.length?formatDate(dates[dates.length-1].snapshot_generated_at):"—"}</strong><span>{t("lastObservation")}</span></div></div>
   {dates.length?<>
    <div className="ob-panel"><h3>{t("timelineLabel")} — {t(metricLabels[metric])}</h3>{dates.length>1?<SeriesChart rows={dates} metric={metric} formatDate={formatDate} format={format}/>:<p>{t("noTime")}</p>}</div>
    <div className="ob-table-scroll"><table className="ob-table"><thead><tr><th>{t("date")}</th><th>{t("metric")}</th><th>{t("value")}</th></tr></thead><tbody>{dates.map((row,i)=><tr key={row.observation_key||i}><td>{formatDate(row.snapshot_generated_at)}</td><td>{t(metricLabels[metric])}</td><td>{format(verifiedCount(row[metric]))}</td></tr>)}</tbody></table></div>
   </>:<p className="ob-panel">{t("noData")}</p>}
   <p className="disclaimer">{t("snapshotOnly")}</p>
  </>}
  {slice&&<p className="research-sources"><strong>{t("sourceNote")}</strong> <a href={`https://github.com/brauliorrs/memoria-audiovisual-rede/blob/main/${mode==="themes"?slice.tema_pais.source:slice.linha_do_tempo_corpus.source}`} target="_blank" rel="noopener noreferrer">CSV / GitHub</a></p>}
  <p><Link href="/observatorio/">{t("back")}</Link></p>
 </section>;
}
