import type {MetadataRoute} from "next";
import {records} from "@/lib/catalog";
import {PUBLIC_ORIGIN} from "@/lib/seo";
/* The 200 KAVI metadata records are admitted. HOLD corpora are never item releases. */
export default function sitemap():MetadataRoute.Sitemap{
 const paths=["/","/en/","/es/","/acervo/","/instituicoes/","/instituicoes/kavi/",
 "/instituicoes/pesquisa/","/metodologia/","/observatorio/","/analises/","/temas/",
 "/series/","/territorios/","/comparar/","/casos/","/indice-acesso/"];
 return [...paths.map(path=>({url:PUBLIC_ORIGIN+path,changeFrequency:"monthly" as const,
  priority:path==="/"?1:path==="/en/"||path==="/es/"?0.9:0.7,
  ...(path==="/"||path==="/en/"||path==="/es/"?{alternates:{languages:{"pt-BR":PUBLIC_ORIGIN+"/",en:PUBLIC_ORIGIN+"/en/",es:PUBLIC_ORIGIN+"/es/"}}}:{})})),
  ...records.map(record=>({url:PUBLIC_ORIGIN+"/acervo/kavi/"+encodeURIComponent(record.id)+"/",changeFrequency:"monthly" as const,priority:0.5}))];
}
