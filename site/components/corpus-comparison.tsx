"use client";

import Link from "next/link";
import {useEffect, useMemo, useState} from "react";
import {decodeResearchSlice, encodeResearchSlice} from "@/lib/research-permalink";
import {researchSnapshotCommit} from "@/lib/research-snapshot";
import {useSiteLocale} from "@/components/site-locale";
import {
  compareDimensions, comparisonMetrics, comparisonSources, historicalSeries, toCsv,
  type ComparisonDimension, type ComparisonMetric, type HistoricalSeries
} from "@/lib/corpus-comparison";

type Tab = "distributions" | "timeline";
const copy = {
  pt: {
    eyebrow:"LABORATÓRIO CIENTÍFICO · MAR",title:"Comparar corpora audiovisuais",
    intro:"Selecione duas ou três fontes para investigar temas, países, plataformas e a evolução da documentação ao longo das coletas. Os resultados provêm dos indicadores históricos do Streamlit, não de mídias republicadas.",
    first:"Fonte 1",second:"Fonte 2",third:"Fonte 3 (opcional)",none:"Sem terceira fonte",
    distribution:"Temas e territórios",timeline:"Séries de observação",dimension:"Dimensão",theme:"Temas",
    country:"Países",platform:"Plataformas",metric:"Indicador",search:"Filtrar termos",
    shared:"Somente termos em 2+ fontes",all:"Todos os termos",term:"Termo",
    occurrences:"Ocorrências",share:"Participação no recorte",download:"Exportar CSV do recorte",
    more:"Mostrar mais",shown:"termos encontrados",noResults:"Nenhum termo encontrado neste recorte.",
    copyLink:"Copiar link desta pesquisa",copied:"Link copiado",copyFailed:"Não foi possível copiar. Use o endereço do navegador.",
    reproducible:"Recorte reproduzível",snapshot:"Revisão das fontes",
    noData:"Esta fonte não tem observações agregadas para a dimensão escolhida.",
    timelineNoData:"Nenhuma observação temporal neste corpus.",
    sourceCoverage:"Cobertura por fonte",labels:"termos",observed:"ocorrências",singleWarning:"Uma observação não demonstra tendência.",
    firstDate:"Primeira coleta",lastDate:"Última coleta",points:"observações",change:"Variação entre primeira e última",
    note:"As distribuições usam denominadores independentes por fonte. A mesma obra pode existir em mais de um catálogo; as classificações podem diferir. As porcentagens mostram a participação de cada termo dentro de sua própria fonte, não uma comparação estatística representativa do mundo. País e plataforma não são cruzados entre si.",
    timeNote:"Cada gráfico tem sua própria escala e datas de coleta. É incorreto interpretar linhas de fontes diferentes como uma série sincronizada; datas de coleta não são datas de produção dos filmes. Uma observação isolada não constitui tendência.",
    disclaimer:"A pesquisa utiliza exclusivamente estatísticas e snapshots históricos. Nenhum título individual, mídia ou ficha de fontes sob HOLD é publicado.",
    provenance:"Arquivo agregado de origem",return:"Voltar ao observatório",
    metricVideo:"Links detectados",metricInstitutions:"Instituições",metricWithVideo:"Instituições com links",
    metricCatalogue:"Itens em catálogo histórico",metricCountries:"Países com registros",
  },
  en: {
    eyebrow:"RESEARCH LAB · MAR",title:"Compare audiovisual corpora",
    intro:"Choose two or three sources to study themes, countries, platforms, and how documented observations evolved across collection runs. Results are Streamlit historical aggregates, not republished media.",
    first:"Source 1",second:"Source 2",third:"Source 3 (optional)",none:"No third source",
    distribution:"Themes and territories",timeline:"Observation series",dimension:"Dimension",theme:"Themes",
    country:"Countries",platform:"Platforms",metric:"Indicator",search:"Filter terms",
    shared:"Terms present in 2+ sources",all:"All terms",term:"Term",
    occurrences:"Occurrences",share:"Share of the source",download:"Export selected CSV",
    more:"Show more",shown:"matching terms",noResults:"No terms match this selection.",
    copyLink:"Copy research link",copied:"Link copied",copyFailed:"Could not copy. Use your browser address bar.",
    reproducible:"Reproducible research slice",snapshot:"Source revision",
    noData:"This source has no historical aggregates for this dimension.",
    timelineNoData:"No historical observations for this source.",
    sourceCoverage:"Coverage by source",labels:"labels",observed:"occurrences",singleWarning:"A single observation cannot establish a trend.",
    firstDate:"First observation",lastDate:"Latest observation",points:"observations",change:"Change from first to latest",
    note:"Each source uses its own denominator. The same work may appear in more than one catalogue, and classifications can differ. Percentages are within-source shares, not a representative worldwide comparison. Country and platform are independent dimensions.",
    timeNote:"Each chart has its own scale and collection dates. Lines from different sources are not synchronized; observation dates are not film production dates. A single observation cannot establish a trend.",
    disclaimer:"This study uses historical aggregate counts and snapshots only. No restricted item titles, media, or individual records are published.",
    provenance:"Source aggregate file",return:"Back to observatory",
    metricVideo:"Detected links",metricInstitutions:"Institutions",metricWithVideo:"Institutions with links",
    metricCatalogue:"Items in historical catalogue",metricCountries:"Countries with records",
  },
  es: {
    eyebrow:"LABORATORIO CIENTÍFICO · MAR",title:"Comparar corpus audiovisuales",
    intro:"Seleccione dos o tres fuentes para estudiar temas, países, plataformas y la evolución de las observaciones documentales. Los datos son agregados históricos de Streamlit, no medios republicados.",
    first:"Fuente 1",second:"Fuente 2",third:"Fuente 3 (opcional)",none:"Sin tercera fuente",
    distribution:"Temas y territorios",timeline:"Series de observación",dimension:"Dimensión",theme:"Temas",
    country:"Países",platform:"Plataformas",metric:"Indicador",search:"Filtrar términos",
    shared:"Términos presentes en 2+ fuentes",all:"Todos los términos",term:"Término",
    occurrences:"Ocurrencias",share:"Proporción dentro de la fuente",download:"Exportar CSV del recorte",
    more:"Mostrar más",shown:"términos encontrados",noResults:"No hay términos para esta selección.",
    copyLink:"Copiar enlace de la investigación",copied:"Enlace copiado",copyFailed:"No se pudo copiar. Use la barra del navegador.",
    reproducible:"Recorte reproducible",snapshot:"Revisión de fuentes",
    noData:"Esta fuente no tiene indicadores agregados en la dimensión elegida.",
    timelineNoData:"No hay observaciones temporales para esta fuente.",
    sourceCoverage:"Cobertura por fuente",labels:"términos",observed:"ocurrencias",singleWarning:"Una observación no demuestra una tendencia.",
    firstDate:"Primera observación",lastDate:"Última observación",points:"observaciones",change:"Cambio entre primera y última",
    note:"Cada fuente utiliza su propio denominador. Una obra puede aparecer en varios catálogos y las clasificaciones pueden diferir. Los porcentajes son proporciones dentro de cada fuente, no una comparación mundial representativa. País y plataforma son dimensiones independientes.",
    timeNote:"Cada gráfico tiene su propia escala y fechas de recopilación. Las fuentes no forman una serie sincronizada; las fechas de recopilación no son de producción de películas. Una sola observación no muestra tendencias.",
    disclaimer:"La investigación utiliza recuentos y snapshots históricos agregados. No se publican títulos, medios ni fichas individuales de fuentes bloqueadas.",
    provenance:"Archivo agregado de origen",return:"Volver al observatorio",
    metricVideo:"Enlaces detectados",metricInstitutions:"Instituciones",metricWithVideo:"Instituciones con enlaces",
    metricCatalogue:"Ítems en catálogo histórico",metricCountries:"Países con registros",
  },
} as const;

function saveCsv(filename:string, rows:(string|number|null|undefined)[][]) {
  const blob=new Blob([toCsv(rows)],{type:"text/csv;charset=utf-8"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=url; a.download=filename; document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}

function SourceSeries({data,formatNumber,formatDate,labels}:{
  data:HistoricalSeries;
  formatNumber:(n:number)=>string;
  formatDate:(date:string)=>string;
  labels:{timelineNoData:string;firstDate:string;lastDate:string;points:string;change:string;provenance:string;singleWarning:string};
}){
  const {points}=data;
  if (!points.length) return <article className="ob-panel"><h3>{data.code.toUpperCase()}</h3><p>{labels.timelineNoData}</p></article>;
  const values=points.map(point=>point.value);
  const min=Math.min(...values), max=Math.max(...values), range=Math.max(1,max-min);
  const coords=points.map((p,i)=>({
    x:35+(i/Math.max(points.length-1,1))*665,
    y:190-(p.value-min)/range*145,
  }));
  const last=points[points.length-1],first=points[0];
  const delta=last.value-first.value;
  return <article className="ob-panel compare-series-card">
    <h3>{data.code.toUpperCase().replaceAll("_"," ")}</h3>
    <p className="compare-series-dates">{labels.firstDate}: {formatDate(first.date)} · {labels.lastDate}: {formatDate(last.date)}</p>
    <div className="compare-series-number"><strong>{formatNumber(last.value)}</strong><span>{points.length} {labels.points}</span></div>
    {points.length>1 ? <>
      <svg viewBox="0 0 740 220" role="img" aria-label={data.code+": "+points.map(p=>formatDate(p.date)+" "+formatNumber(p.value)).join("; ")}>
        <line x1="35" y1="190" x2="710" y2="190" stroke="currentColor" strokeOpacity=".2"/>
        <polyline fill="none" stroke="#147866" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"
          points={coords.map(p=>p.x+","+p.y).join(" ")}/>
        {coords.map((p,i)=><circle key={points[i].key||i} cx={p.x} cy={p.y} r="4" fill="#147866"/>)}
        <text x="35" y="22" fontSize="14" fill="currentColor">{formatNumber(max)}</text>
        <text x="35" y="214" fontSize="14" fill="currentColor">{formatNumber(min)}</text>
      </svg>
      <p>{labels.change}: <strong>{delta>0?"+":""}{formatNumber(delta)}</strong></p>
    </> : <p>{labels.singleWarning}</p>}
    {data.sourcePath&&<p className="compare-provenance"><a href={"https://github.com/brauliorrs/memoria-audiovisual-rede/blob/"+researchSnapshotCommit+"/"+data.sourcePath} target="_blank" rel="noopener noreferrer">{labels.provenance}</a></p>}
  </article>;
}

export function CorpusComparison() {
  const {locale,setLocale}=useSiteLocale();
  const t=copy[locale];
  const number=new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US");
  const dateFormatter=new Intl.DateTimeFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-GB",
    {year:"numeric",month:"short",day:"numeric",timeZone:"UTC"});
  const formatDate=(date:string)=>dateFormatter.format(new Date(date));
  const formatNumber=(n:number)=>number.format(n);
  const initialA=comparisonSources.includes("ape")?"ape":comparisonSources[0]??"";
  const initialB=comparisonSources.includes("eye")?"eye":comparisonSources.find(c=>c!==initialA)??"";
  const initialC=comparisonSources.includes("europeana")?"europeana":"";
  const [sources,setSources]=useState<[string,string,string]>([initialA,initialB,initialC]);
  const [tab,setTab]=useState<Tab>("distributions");
  const [dimension,setDimension]=useState<ComparisonDimension>("theme");
  const [metric,setMetric]=useState<ComparisonMetric>("video_links_total");
  const [query,setQuery]=useState("");
  const [sharedOnly,setSharedOnly]=useState(false);
  const [shown,setShown]=useState(30);
  const [urlReady,setUrlReady]=useState(false);
  const [copyStatus,setCopyStatus]=useState<"idle"|"copied"|"failed">("idle");

  // The same URL restores the entire filtered study without touching the server.
  useEffect(()=>{
    const params=new URLSearchParams(window.location.search);
    if(params.has("a")||params.has("b")||params.has("c")||params.has("view")||params.has("dimension")){
      const saved=decodeResearchSlice(params);
      setSources(saved.sources);
      setTab(saved.view);
      setDimension(saved.dimension);
      setMetric(saved.metric);
      setQuery(saved.query);
      setSharedOnly(saved.sharedOnly);
      if(params.has("lang"))setLocale(saved.locale);
    }
    setUrlReady(true);
  // Restore once on mount; later changes are synchronized in the effect below.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);
  useEffect(()=>{
    if(!urlReady)return;
    const params=encodeResearchSlice({sources,view:tab,dimension,metric,query,sharedOnly,locale});
    window.history.replaceState(window.history.state,"",window.location.pathname+"?"+params.toString()+window.location.hash);
    setCopyStatus("idle");
  },[urlReady,sources,tab,dimension,metric,query,sharedOnly,locale]);
  const copyResearchLink=async()=>{
    try{await navigator.clipboard.writeText(window.location.href);setCopyStatus("copied");}
    catch{setCopyStatus("failed");}
  };
  const selected=sources.filter(Boolean);
  const {distributions,entries}=useMemo(()=>compareDimensions(selected,dimension),[sources,dimension]);
  const search=query.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim();
  const filtered=entries.filter(item=>(!sharedOnly||item.presentIn>=2)
    &&(!search||item.label.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().includes(search)));
  const series=selected.map(source=>historicalSeries(source,metric));

  const setSource=(index:number,value:string)=>{
    setSources(prev=>{const next:[string,string,string]=[...prev];next[index]=value;return next;});
    setShown(30);
  };
  const exportAggregate=()=>{
    if(tab==="timeline"){
      const rows:(string|number|null|undefined)[][]=[
        ["corpus","observation_date","metric","value","aggregate_source_file","source_snapshot_commit"],
      ];
      series.forEach(s=>s.points.forEach(p=>rows.push([s.code,p.date,metric,p.value,s.sourcePath,researchSnapshotCommit])));
      saveCsv("mar-comparacao-series.csv",rows);
    }else{
      const rows:(string|number|null|undefined)[][]=[
        ["dimension","label","corpus","occurrences","share_within_corpus","source_denominator","source_file","source_snapshot_commit"],
      ];
      filtered.forEach(row=>distributions.forEach(s=>{
        const cell=row.bySource[s.code];
        if(cell!==null&&cell!==undefined)rows.push([
          dimension,row.label,s.code,cell.count,cell.share.toFixed(6),s.total,s.sourcePath,researchSnapshotCommit
        ]);
      }));
      saveCsv("mar-comparacao-"+dimension+".csv",rows);
    }
  };

  return <section className="compare-workbench">
    <p className="eyebrow">{t.eyebrow}</p>
    <h1>{t.title}</h1>
    <p className="page-lede">{t.intro}</p>
    <div className="compare-repro-box" aria-label={t.reproducible}>
      <div><strong>{t.reproducible}</strong><span>{t.snapshot}: <code>{researchSnapshotCommit.slice(0,12)}</code></span></div>
      <button type="button" className="ob-case-toggle" onClick={copyResearchLink}>{t.copyLink}</button>
      {copyStatus!=="idle"&&<p role="status">{copyStatus==="copied"?t.copied:t.copyFailed}</p>}
    </div>
    <div className="ob-filter-panel compare-source-selectors">
      {sources.map((source,index)=><div key={index}>
        <label htmlFor={"compare-source-"+index}>{[t.first,t.second,t.third][index]}</label>
        <select id={"compare-source-"+index} value={source}
          onChange={event=>setSource(index,event.target.value)}>
          {index===2&&<option value="">{t.none}</option>}
          {comparisonSources.map(code=><option key={code} value={code} disabled={sources.some((selected,i)=>i!==index&&selected===code)}>
            {code.toUpperCase().replaceAll("_"," ")}
          </option>)}
        </select>
      </div>)}
    </div>
    <div className="ob-viewbar">
      <div className="ob-viewtabs" role="group" aria-label={t.title}>
        <button type="button" aria-pressed={tab==="distributions"} onClick={()=>setTab("distributions")}>{t.distribution}</button>
        <button type="button" aria-pressed={tab==="timeline"} onClick={()=>setTab("timeline")}>{t.timeline}</button>
      </div>
      <button type="button" className="ob-case-toggle" onClick={exportAggregate}>{t.download}</button>
    </div>
    {tab==="distributions"?<>
      <div className="ob-filter-panel compare-analysis-controls">
        <div><label htmlFor="compare-dimension">{t.dimension}</label><select id="compare-dimension"
          value={dimension} onChange={event=>{setDimension(event.target.value as ComparisonDimension);setShown(30);}}>
          <option value="theme">{t.theme}</option><option value="country">{t.country}</option>
          <option value="platform">{t.platform}</option></select></div>
        <div><label htmlFor="compare-filter">{t.search}</label><input id="compare-filter"
          value={query} onChange={event=>{setQuery(event.target.value);setShown(30);}}/></div>
        <div><label htmlFor="compare-shared">{t.sourceCoverage}</label><select id="compare-shared"
          value={sharedOnly?"shared":"all"} onChange={event=>{setSharedOnly(event.target.value==="shared");setShown(30);}}>
          <option value="all">{t.all}</option><option value="shared">{t.shared}</option>
        </select></div>
      </div>
      <div className="ob-group-list compare-coverage">
        {distributions.map(source=><article className="ob-panel" key={source.code}>
          <h2>{source.code.toUpperCase().replaceAll("_"," ")}</h2>
          <p><strong>{formatNumber(source.labels)}</strong> {t.labels} · <strong>{formatNumber(source.total)}</strong> {t.observed}</p>
          {!source.available&&<p>{t.noData}</p>}
          {source.sourcePath&&<a href={"https://github.com/brauliorrs/memoria-audiovisual-rede/blob/"+researchSnapshotCommit+"/"+source.sourcePath}
            target="_blank" rel="noopener noreferrer">{t.provenance}</a>}
        </article>)}
      </div>
      <p className="access-result-count">{formatNumber(filtered.length)} {t.shown}</p>
      {filtered.length>0?<div className="ob-table-scroll"><table className="ob-table compare-table">
        <thead><tr><th>{t.term}</th>{distributions.map(s=><th key={s.code}>{s.code.toUpperCase().replaceAll("_"," ")}</th>)}</tr></thead>
        <tbody>{filtered.slice(0,shown).map(item=><tr key={item.label}>
          <td><strong>{item.label}</strong></td>
          {distributions.map(s=>{const cell=item.bySource[s.code];return <td key={s.code}>
            {cell? <div className="compare-cell"><strong>{formatNumber(cell.count)}</strong>
              <span>{number.format(cell.share*100)}%</span>
              <div className="ob-bar-track" role="img" aria-label={item.label+": "+number.format(cell.share*100)+"%"}>
                <span style={{width:Math.min(100,cell.share*100)+"%"}}/>
              </div></div> : <span aria-label="Sem ocorrência nesta fonte">—</span>}
          </td>})}
        </tr>)}</tbody>
      </table></div>:<p className="ob-panel">{t.noResults}</p>}
      {filtered.length>shown&&<button type="button" className="ob-case-toggle compare-more"
        onClick={()=>setShown(prev=>prev+30)}>{t.more} ({formatNumber(filtered.length-shown)})</button>}
      <p className="disclaimer">{t.note}</p>
    </>:<>
      <div className="ob-filter-panel"><div><label htmlFor="compare-metric">{t.metric}</label>
        <select id="compare-metric" value={metric} onChange={event=>setMetric(event.target.value as ComparisonMetric)}>
          {comparisonMetrics.map(m=><option key={m} value={m}>{({
            video_links_total:t.metricVideo,institutions:t.metricInstitutions,
            institutions_with_video_links:t.metricWithVideo,
            videos_in_curatorial_catalog:t.metricCatalogue,
            countries_with_videos:t.metricCountries
          } as Record<ComparisonMetric,string>)[m]}</option>)}
        </select></div></div>
      <div className="ob-group-list compare-series-grid">
        {series.map(source=><SourceSeries key={source.code} data={source} formatNumber={formatNumber}
          formatDate={formatDate} labels={t}/>)}
      </div>
      <p className="disclaimer">{t.timeNote}</p>
    </>}
    <p className="disclaimer">{t.disclaimer}</p>
    <p><Link href="/observatorio/">{t.return}</Link></p>
  </section>;
}
