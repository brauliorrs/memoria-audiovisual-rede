"use client";

import Link from "next/link";
import {useMemo, useState} from "react";
import world from "@/data/world-110m-geometry.json";
import {useSiteLocale} from "@/components/site-locale";
import {getResearchSlice, researchSourceCodes, verifiedCount} from "@/lib/research-slices";
import {researchSnapshotCommit} from "@/lib/research-snapshot";

const wording = {
  pt:{
    title:"Mapa territorial da pesquisa",intro:"Visualize a distribuição de ocorrências documentais por país no corpus selecionado. Os dados são cruzamentos históricos entre temas e países produzidos pelo Streamlit.",
    source:"Fonte histórica",theme:"Tema",all:"Todos os temas",records:"Ocorrências classificadas",countries:"Países observados",
    mapped:"Países com geometria",noGeometry:"Países sem geometria nesta escala",noData:"Sem dados territoriais neste recorte",
    table:"Distribuição por país",territory:"País / território",count:"Ocorrências",map:"Mapa mundial de países",
    legend:"Países destacados representam registros classificados; intensidade proporcional dentro desta fonte.",
    note:"O país indicado nos metadados não identifica necessariamente onde o filme foi produzido, gravado ou exibido. A análise não representa a produção audiovisual total, nem cruza países com plataformas. Países pequenos e alguns territórios podem não ter polígonos na escala 1:110 milhões; suas ocorrências permanecem na tabela.",
    geometry:"Limites cartográficos: Natural Earth (domínio público), 1:110m, via geo-boundaries-world-110m.",
    sourceFile:"Arquivo agregado de origem",copyright:"A visualização não reproduz obras, vídeos ou fichas individuais sob HOLD.",
    return:"Voltar aos temas",explore:"Comparar com outras fontes",
  },
  en:{
    title:"Research territories map",intro:"Explore historically classified occurrences by country in the selected corpus, using the Streamlit theme-by-country aggregation.",
    source:"Historical source",theme:"Theme",all:"All themes",records:"Classified occurrences",countries:"Observed countries",
    mapped:"Countries with geometry",noGeometry:"Countries without geometry at this scale",noData:"No territorial data for this selection",
    table:"Distribution by country",territory:"Country / territory",count:"Occurrences",map:"World country map",
    legend:"Highlighted countries represent classified observations; intensity is proportional within this source.",
    note:"The country recorded in metadata does not necessarily identify where a film was produced, recorded, or shown. These data are not a global production census and do not cross countries with platforms. Small countries and territories may have no polygon at the 1:110 million scale; their counts remain in the table.",
    geometry:"Boundaries: Natural Earth (public domain), 1:110m, via geo-boundaries-world-110m.",
    sourceFile:"Original aggregate dataset",copyright:"This visualization does not republish works, media or individual records on HOLD.",
    return:"Back to themes",explore:"Compare with other sources",
  },
  es:{
    title:"Mapa territorial de investigación",intro:"Explore las ocurrencias históricas clasificadas por país en el corpus seleccionado, a partir del cruce tema×país de Streamlit.",
    source:"Fuente histórica",theme:"Tema",all:"Todos los temas",records:"Ocurrencias clasificadas",countries:"Países observados",
    mapped:"Países con geometría",noGeometry:"Países sin geometría a esta escala",noData:"No hay datos territoriales para esta selección",
    table:"Distribución por país",territory:"País / territorio",count:"Ocurrencias",map:"Mapa mundial de países",
    legend:"Los países resaltados representan registros clasificados; la intensidad es relativa a esta fuente.",
    note:"El país de los metadatos no indica necesariamente dónde se produjo, grabó o exhibió la obra. No es un censo mundial y no cruza países con plataformas. Algunos países pequeños y territorios no tienen polígonos a escala 1:110 millones; sus recuentos se conservan en la tabla.",
    geometry:"Límites cartográficos: Natural Earth (dominio público), 1:110m, vía geo-boundaries-world-110m.",
    sourceFile:"Archivo agregado de origen",copyright:"No se republican obras, vídeos ni fichas individuales de fuentes en HOLD.",
    return:"Volver a temas",explore:"Comparar con otras fuentes",
  },
} as const;

const geometryNames = new Set(world.geometries.map(shape=>shape.name));

export function TerritorialMap(){
  const {locale}=useSiteLocale();
  const t=wording[locale];
  const [source,setSource]=useState(researchSourceCodes.includes("ape")?"ape":researchSourceCodes[0]??"");
  const [theme,setTheme]=useState("");
  const [focusedCountry,setFocusedCountry]=useState("");
  const [showAll,setShowAll]=useState(false);
  const sourceSlice=getResearchSlice(source);
  const themes=sourceSlice?[...new Set(sourceSlice.tema_pais.rows.map(row=>row.tema))].filter(Boolean).sort().map(name=>({name})):[];
  const activeTheme=themes.some(item=>item.name===theme)?theme:"";
  const summary=useMemo(()=>{
    const counts=new Map<string,number>();
    if(sourceSlice)for(const row of sourceSlice.tema_pais.rows){
      if(activeTheme&&row.tema!==activeTheme)continue;
      const country=row.pais.trim();
      const amount=verifiedCount(row.total);
      if(country&&amount>0)counts.set(country,(counts.get(country)??0)+amount);
    }
    const rows=[...counts].map(([name,count])=>({name,count})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
    return {rows,total:rows.reduce((n,r)=>n+r.count,0),byName:counts,unmapped:rows.filter(row=>!geometryNames.has(row.name))};
  },[sourceSlice,activeTheme]);
  const max=Math.max(1,...summary.rows.map(row=>row.count));
  const number=new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US");
  const selectedCountry=summary.rows.find(row=>row.name===focusedCountry);
  return <section className="territorial-workbench">
    <p className="eyebrow">MAR · GEOGRAPHICAL RESEARCH</p>
    <h1>{t.title}</h1>
    <p className="page-lede">{t.intro}</p>
    <div className="ob-filter-panel territorial-filters">
      <div><label htmlFor="territory-source">{t.source}</label><select id="territory-source"
        value={source} onChange={event=>{setSource(event.target.value);setTheme("");setFocusedCountry("");setShowAll(false);}}>
        {researchSourceCodes.map(code=><option key={code} value={code}>{code.toUpperCase().replaceAll("_"," ")}</option>)}
      </select></div>
      <div><label htmlFor="territory-theme">{t.theme}</label><select id="territory-theme"
        value={activeTheme} onChange={event=>{setTheme(event.target.value);setFocusedCountry("");}}>
        <option value="">{t.all}</option>
        {themes.map(item=><option key={item.name} value={item.name}>{item.name}</option>)}
      </select></div>
    </div>
    <div className="ob-kpis territorial-kpis">
      <div><strong>{number.format(summary.total)}</strong><span>{t.records}</span></div>
      <div><strong>{number.format(summary.rows.length)}</strong><span>{t.countries}</span></div>
      <div><strong>{number.format(summary.rows.length-summary.unmapped.length)}</strong><span>{t.mapped}</span></div>
    </div>
    <article className="ob-panel territorial-map-panel">
      <h2>{t.map}</h2>
      <p className="disclaimer">{t.legend}</p>
      <svg viewBox={world.viewBox} role="img" aria-label={t.map} className="territorial-svg">
        <rect x="0" y="0" width="900" height="450" rx="12" fill="#f2f7f4"/>
        {world.geometries.map(shape=>{
          const count=summary.byName.get(shape.name)??0;
          const rate=count/max;
          const fill=count>0?`hsl(167 60% ${(64-43*Math.sqrt(rate)).toFixed(1)}%)`:"#dbe6df";
          return <path key={shape.iso+shape.name} d={shape.d}
            fill={fill} stroke="#fff" strokeWidth=".5" strokeLinejoin="round"
            tabIndex={count>0?0:undefined}
            aria-label={count>0?`${shape.name}: ${number.format(count)}`:shape.name}
            onFocus={()=>setFocusedCountry(shape.name)} onBlur={()=>setFocusedCountry("")}
            onMouseEnter={()=>setFocusedCountry(shape.name)} onMouseLeave={()=>setFocusedCountry("")}>
            <title>{shape.name}: {number.format(count)}</title>
          </path>;
        })}
      </svg>
      {selectedCountry&&<p role="status" className="territorial-selected"><strong>{selectedCountry.name}</strong> — {number.format(selectedCountry.count)} {t.count.toLowerCase()}</p>}
      {summary.rows.length===0&&<p>{t.noData}</p>}
      <p className="disclaimer">{t.note}</p>
      <p className="disclaimer">{t.geometry}</p>
    </article>
    <article className="ob-panel">
      <h2>{t.table}</h2>
      {summary.rows.length>0?<div className="ob-table-scroll"><table className="ob-table">
        <thead><tr><th>{t.territory}</th><th>{t.count}</th></tr></thead>
        <tbody>{summary.rows.slice(0,showAll?summary.rows.length:18).map(row=><tr key={row.name}>
          <td>{row.name}{!geometryNames.has(row.name)?" · *":""}</td>
          <td>{number.format(row.count)}</td>
        </tr>)}</tbody>
      </table></div>:<p>{t.noData}</p>}
      {!showAll&&summary.rows.length>18&&<button type="button" className="ob-case-toggle" onClick={()=>setShowAll(true)}>+ {summary.rows.length-18}</button>}
      {summary.unmapped.length>0&&<p className="disclaimer">* {t.noGeometry}: {summary.unmapped.map(x=>x.name).join(", ")}.</p>}
    </article>
    <p className="research-sources">{t.sourceFile}: <a target="_blank" rel="noopener noreferrer"
      href={`https://github.com/brauliorrs/memoria-audiovisual-rede/blob/${researchSnapshotCommit}/${sourceSlice?.tema_pais.source??""}`}>
      {sourceSlice?.tema_pais.source??"—"}</a></p>
    <p className="disclaimer">{t.copyright}</p>
    <p><Link href="/temas/">{t.return}</Link> · <Link href="/comparar/">{t.explore}</Link></p>
  </section>;
}
