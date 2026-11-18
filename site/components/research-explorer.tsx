"use client";
import {useMemo,useState} from "react";
import type {AnalyticRow,ResearchDimension} from "@/lib/research-dimensions";

type Language="pt"|"en"|"es";
const lex={
 pt:{title:"Pesquisa temática e territorial",topic:"Temas",country:"País × tema",platform:"Plataforma × tema",archive:"Tipo de arquivo × tema",timeline:"Série de observações",institution:"Instituições",all:"Todos",search:"Filtrar linhas",count:"Ocorrências",note:"Séries de snapshots de coleta, não datas de produção audiovisual. Os cruzamentos são contagens históricas agregadas, sem autorização de republicação de objetos.",empty:"Nenhuma linha histórica disponível para este recorte.",date:"Data da observação"},
 en:{title:"Thematic and territorial research",topic:"Themes",country:"Country × theme",platform:"Platform × theme",archive:"Archive type × theme",timeline:"Observation series",institution:"Institutions",all:"All",search:"Filter rows",count:"Occurrences",note:"Collection snapshots, not audiovisual production dates. These are historical aggregate counts, not permission to republish objects.",empty:"No historical observations for this selection.",date:"Observation date"},
 es:{title:"Investigación temática y territorial",topic:"Temas",country:"País × tema",platform:"Plataforma × tema",archive:"Tipo de archivo × tema",timeline:"Serie de observaciones",institution:"Instituciones",all:"Todos",search:"Filtrar filas",count:"Ocurrencias",note:"Instantáneas de recolección, no fechas de producción audiovisual. Son recuentos históricos agregados, sin autorización para republicar objetos.",empty:"No hay observaciones históricas para esta selección.",date:"Fecha de observación"}
} as const;
const keys:ResearchDimension[]=["resumo_temas","tema_pais","tema_plataforma","tema_tipo_arquivo","linha_do_tempo_corpus","resumo_instituicoes"];
const labels=["topic","country","platform","archive","timeline","institution"] as const;
const num=(v:string)=>Number(v||0)||0;
export function ResearchExplorer({data}:{data:Record<ResearchDimension,AnalyticRow[]>}){
 const [lang,setLang]=useState<Language>("pt"),[view,setView]=useState<ResearchDimension>("resumo_temas"),[query,setQuery]=useState(""),[limit,setLimit]=useState(40);
 const t=lex[lang];
 const rows=useMemo(()=>data[view].filter(r=>Object.values(r).join(" ").toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())).slice(0,limit),[data,view,query,limit]);
 const timeline=view==="linha_do_tempo_corpus";
 const columns=timeline?["snapshot_generated_at","institutions","institutions_with_video_links","video_links_total"]:view==="resumo_instituicoes"?Object.keys(rows[0]??{}).slice(0,5):Object.keys(rows[0]??{}).slice(0,4);
 const total=rows.reduce((sum,r)=>sum+num(r.total),0),max=Math.max(1,...rows.map(r=>num(r.total)));
 return <section className="ob-panel" aria-label={t.title}>
 <div className="ob-viewbar"><h2>{t.title}</h2><div className="ob-viewtabs" role="group" aria-label="Language / Idioma"><button aria-pressed={lang==="pt"} onClick={()=>setLang("pt")}>PT</button><button aria-pressed={lang==="en"} onClick={()=>setLang("en")}>EN</button><button aria-pressed={lang==="es"} onClick={()=>setLang("es")}>ES</button></div></div>
 <div className="ob-viewtabs" role="group" aria-label={t.title}>{keys.map((k,i)=><button key={k} aria-pressed={view===k} onClick={()=>{setView(k);setQuery("");setLimit(40)}}>{t[labels[i]]}</button>)}</div>
 <div className="ob-filter-panel"><div><label htmlFor="research-filter">{t.search}</label><input id="research-filter" value={query} onChange={e=>setQuery(e.target.value)} /></div></div>
 {rows.length===0?<p>{t.empty}</p>:<><p className="access-result-count">{rows.length} / {data[view].length} · {timeline?t.date:t.count}{!timeline?": "+new Intl.NumberFormat(lang==="pt"?"pt-BR":lang==="es"?"es-ES":"en-US").format(total):""}</p>
 {!timeline&&view!=="resumo_instituicoes"&&<div className="ob-bars">{rows.slice(0,15).map((r,i)=><div className="ob-bar-item" key={i}><div className="ob-bar-label"><span>{[r.tema,r.pais,r.plataforma,r.tipo_arquivo].filter(Boolean).join(" · ")}</span><strong>{r.total}</strong></div><div className="ob-bar-track"><span style={{width:`${100*num(r.total)/max}%`}}/></div></div>)}</div>}
 <div className="ob-table-scroll"><table className="ob-table"><thead><tr>{columns.map(k=><th key={k}>{k.replaceAll("_"," ")}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{columns.map(k=><td key={k}>{r[k]??"—"}</td>)}</tr>)}</tbody></table></div>
 {rows.length<data[view].length&&<button className="ob-case-toggle" onClick={()=>setLimit(v=>v+50)}>+50</button>}</>}
 <p className="disclaimer">{t.note}</p>
 </section>;
}
