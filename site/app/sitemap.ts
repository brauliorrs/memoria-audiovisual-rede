export const dynamic="force-static";
import type {MetadataRoute} from "next";
import {SITE_ORIGIN,STATIC_ROUTES,canonicalPath,localePagePath} from "@/lib/seo";
import {records} from "@/lib/catalog";
import {corpusList} from "@/lib/scientific-observatory";
import {researchSourceCodes} from "@/lib/research-dimensions";
import {institutionalProfiles} from "@/lib/institutional-profiles";

/**
 * URLs already served by the MAR site only. This is not a publication gate:
 * catalog items come EXCLUSIVELY from the approved 200-record KAVI index.
 * Historical corpus and institutional pages contain aggregate/administrative
 * observations, not newly released audiovisual item records.
 */
export default function sitemap():MetadataRoute.Sitemap{
 const paths=[
  ...records.map(item=>`/acervo/kavi/${encodeURIComponent(item.id)}/`),
  ...corpusList.map(item=>`/observatorio/${encodeURIComponent(item.code)}/`),
  ...researchSourceCodes().map(code=>`/pesquisa/${encodeURIComponent(code)}/`),
  ...institutionalProfiles.map(item=>`/instituicoes/pesquisa/${encodeURIComponent(item.source)}/${encodeURIComponent(item.id.split(":")[1])}/`),
 ];
 const languages=["pt","en","es"] as const;
 const multilingual=STATIC_ROUTES.flatMap(path=>languages.map(locale=>({
  url:SITE_ORIGIN+localePagePath(path,locale),
  alternates:{languages:{
   "pt-BR":SITE_ORIGIN+localePagePath(path,"pt"),
   "en":SITE_ORIGIN+localePagePath(path,"en"),
   "es":SITE_ORIGIN+localePagePath(path,"es"),
   "x-default":SITE_ORIGIN+localePagePath(path,"pt"),
  }},
 })));
 const unlocalized=[...new Set(paths)].sort().map(path=>({
  url:SITE_ORIGIN+canonicalPath(path),
 }));
 return [...multilingual,...unlocalized].sort((a,b)=>a.url.localeCompare(b.url));
}
