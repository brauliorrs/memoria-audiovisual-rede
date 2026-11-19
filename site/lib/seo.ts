import type {Metadata} from "next";
import type {SiteLocale} from "@/components/site-locale";

/** One canonical host only; no preview deployment domains or duplicate Vercel projects. */
export const SITE_ORIGIN="https://mar-public-site.vercel.app";
export const STATIC_ROUTES=[
 "/","/acervo/","/instituicoes/","/instituicoes/kavi/","/metodologia/",
 "/observatorio/","/analises/","/temas/","/territorios/","/series/",
 "/comparar/","/casos/","/indice-acesso/","/instituicoes/pesquisa/",
] as const;
export type StaticRoute=typeof STATIC_ROUTES[number];
type SeoDescription={title:string;description:string};

/**
 * Language-specific editorial metadata drafts. The canonical HTML for existing
 * static routes is currently pt-BR; EN/ES are client-side translations.
 * Do NOT emit hreflang pointing three languages to one URL: when actual
 * crawlable locale-specific paths exist, use these strings there.
 */
export const localizedSeo:Record<SiteLocale,Record<StaticRoute,SeoDescription>>={
 pt:{
 "/":{title:"Memória Audiovisual em Rede — observatório científico",description:"Explore fontes institucionais, indicadores históricos e o catálogo documental autorizado do MAR, com transparência metodológica e rastreabilidade."},
 "/acervo/":{title:"Catálogo público de fichas audiovisuais",description:"Consulte 200 fichas KAVI/Finna aprovadas para publicação de metadados, com links de origem e avisos sobre direitos e reprodução não verificados."},
 "/instituicoes/":{title:"Instituições e corpora audiovisuais",description:"Conheça instituições e fontes mapeadas pelo MAR, distinguindo conectores técnicos de fichas autorizadas para publicação."},
 "/instituicoes/kavi/":{title:"KAVI / Finna — fichas documentais",description:"Índice parcial de 200 fichas KAVI com registros na origem, data da observação, SHA-256 e ressalvas sobre direitos e revisão científica."},
 "/metodologia/":{title:"Metodologia científica e proveniência",description:"Entenda os critérios de proveniência, revisão documental, direitos e publicação controlada dos indicadores e metadados do MAR."},
 "/observatorio/":{title:"Observatório científico de memória audiovisual",description:"Explore indicadores históricos agregados por corpus e instituição sem confundir coleta, consulta na origem e autorização de publicação."},
 "/analises/":{title:"Análises e relatórios científicos por fonte",description:"Compare relatórios históricos documentais por fonte, com denominadores independentes e informações de proveniência."},
 "/temas/":{title:"Temas, países e plataformas audiovisuais",description:"Explore dimensões históricas de pesquisa por fonte; cruzamentos independentes não devem ser interpretados como relações não observadas."},
 "/territorios/":{title:"Mapa territorial dos acervos",description:"Mapa de indicadores agregados de tema e país, com geometria Natural Earth, recortes documentais e rastreabilidade por corpus."},
 "/series/":{title:"Séries temporais de observação",description:"Consulte datas de coleta e indicadores históricos; observações não são cronologias de produção cinematográfica nem dados ao vivo."},
 "/comparar/":{title:"Comparação científica entre corpora",description:"Compare duas ou três fontes audiovisuais com recortes reproduzíveis, proveniência e exportação somente de indicadores agregados."},
 "/casos/":{title:"Casos documentados em pesquisa audiovisual",description:"Examine casos institucionais documentados e suas limitações sem interpretar evidências de acesso como autorização para republicação."},
 "/indice-acesso/":{title:"Índice de Dados Públicos e restrições",description:"Diferencie indicadores históricos, acesso institucional e as 200 fichas efetivamente autorizadas no site público do MAR."},
 "/instituicoes/pesquisa/":{title:"Pesquisa sobre instituições audiovisuais",description:"Pesquise perfis institucionais históricos e links documentais com indicação de limitações, proveniência e ausência de hospedagem de vídeos."},
 },
 en:{
 "/":{title:"Networked Audiovisual Memory — research observatory",description:"Explore institutional sources, historical indicators and MAR's authorized documentary catalogue, with methodological transparency and traceable provenance."},
 "/acervo/":{title:"Public audiovisual record catalogue",description:"Browse 200 KAVI/Finna records approved for metadata publication, with links to their source and notices about unverified media rights and playback."},
 "/instituicoes/":{title:"Audiovisual institutions and corpora",description:"Explore institutions and sources surveyed by MAR, distinguishing technical connectors from records authorized for publication."},
 "/instituicoes/kavi/":{title:"KAVI / Finna — documentary records",description:"Partial index of 200 KAVI records with original-source links, observation date, SHA-256 and cautions about scientific review and rights."},
 "/metodologia/":{title:"Scientific methodology and provenance",description:"Read MAR's provenance, documentary review, media-rights and controlled publication principles."},
 "/observatorio/":{title:"Audiovisual memory research observatory",description:"Explore historical aggregate indicators by corpus and institution without confusing collection, original-source access and publication approval."},
 "/analises/":{title:"Scientific analysis and source reports",description:"Compare historical documentary reports with independent denominators and source provenance."},
 "/temas/":{title:"Audiovisual themes, countries and platforms",description:"Examine source-specific historical dimensions without inferring relationships absent from the observations."},
 "/territorios/":{title:"Territorial map of audiovisual archives",description:"Explore aggregate theme and country indicators with Natural Earth geometry and corpus-level traceability."},
 "/series/":{title:"Observation time series",description:"Explore collection dates and historical indicators, not film production timelines or real-time data."},
 "/comparar/":{title:"Scientific cross-corpus comparison",description:"Compare two or three audiovisual sources using reproducible selections, provenance and aggregate-only CSV export."},
 "/casos/":{title:"Documented cases in audiovisual research",description:"Explore institutional research cases and limitations without treating access evidence as republication permission."},
 "/indice-acesso/":{title:"Public Data Access Index and restrictions",description:"Distinguish historical indicators, institutional access and the 200 records actually approved for MAR's public site."},
 "/instituicoes/pesquisa/":{title:"Audiovisual institutional research",description:"Browse historical institutional profiles and documentary links with provenance, access cautions and no video hosting."},
 },
 es:{
 "/":{title:"Memoria Audiovisual en Red — observatorio científico",description:"Explore fuentes institucionales, indicadores históricos y el catálogo documental autorizado del MAR, con transparencia metodológica y trazabilidad."},
 "/acervo/":{title:"Catálogo público de fichas audiovisuales",description:"Consulte 200 fichas KAVI/Finna aprobadas para publicar metadatos, con enlaces de origen y avisos sobre derechos y reproducción no verificados."},
 "/instituicoes/":{title:"Instituciones y corpus audiovisuales",description:"Conozca instituciones y fuentes estudiadas por MAR, diferenciando conectores técnicos de fichas autorizadas para publicación."},
 "/instituicoes/kavi/":{title:"KAVI / Finna — fichas documentales",description:"Índice parcial de 200 fichas KAVI con enlaces de origen, fecha de observación, SHA-256 y advertencias sobre derechos y revisión científica."},
 "/metodologia/":{title:"Metodología científica y procedencia",description:"Conozca los criterios de procedencia, revisión documental, derechos y publicación controlada de datos del MAR."},
 "/observatorio/":{title:"Observatorio de memoria audiovisual",description:"Explore indicadores históricos agregados sin confundir recopilación, consulta de origen y autorización para publicar."},
 "/analises/":{title:"Análisis e informes científicos por fuente",description:"Compare informes documentales históricos, con denominadores independientes y procedencia documentada."},
 "/temas/":{title:"Temas, países y plataformas audiovisuales",description:"Examine dimensiones históricas por fuente sin deducir relaciones no observadas."},
 "/territorios/":{title:"Mapa territorial de archivos audiovisuales",description:"Mapa de indicadores agregados de tema y país con geometría Natural Earth y trazabilidad por corpus."},
 "/series/":{title:"Series temporales de observación",description:"Consulte fechas de recopilación e indicadores históricos, no cronologías de producción ni datos en tiempo real."},
 "/comparar/":{title:"Comparación científica de corpus",description:"Compare dos o tres fuentes audiovisuales con filtros reproducibles, procedencia y exportación de indicadores agregados solamente."},
 "/casos/":{title:"Casos documentados de investigación audiovisual",description:"Examine casos institucionales y sus límites sin interpretar las pruebas de acceso como permiso de republicación."},
 "/indice-acesso/":{title:"Índice de Acceso a Datos Públicos y restricciones",description:"Distinga indicadores históricos, acceso institucional y las 200 fichas efectivamente aprobadas para el sitio MAR."},
 "/instituicoes/pesquisa/":{title:"Investigación de instituciones audiovisuales",description:"Explore perfiles históricos y enlaces documentales con procedencia, límites de acceso y sin alojamiento de vídeos."},
 }
};

export function canonicalPath(path:string):string{
 if(!path.startsWith("/")||path.startsWith("//")||/[?#]/.test(path))throw new Error("Invalid canonical route");
 return path.endsWith("/")?path:path+"/";
}

export function pageSeo(path:StaticRoute):Metadata{
 const copy=localizedSeo.pt[path];
 return {
  title:copy.title,
  description:copy.description,
  alternates:{canonical:canonicalPath(path)},
  openGraph:{type:"website",url:canonicalPath(path),title:copy.title,description:copy.description},
 };
}

/** Canonical for already published, static dynamic routes (source IDs preserved). */
export function recordSeo(path:string,title:string,description:string):Metadata{
 return {title,description,alternates:{canonical:canonicalPath(path)},
  openGraph:{type:"article",url:canonicalPath(path),title,description}};
}
