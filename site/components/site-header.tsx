"use client";

import Link from "next/link";
import {useSiteLocale,type SiteLocale} from "@/components/site-locale";

export function SiteHeader(){
 const {locale,setLocale,t}=useSiteLocale();
 return <header className="site-header">
  <div className="shell header-inner">
   <Link className="brand" href="/" aria-label="MAR — home"><span className="brand-mark" aria-hidden="true"><span className="brand-mark-center"/></span><span className="brand-name"><strong>MAR<span className="brand-dot">.</span></strong><small>{t("brand")}</small></span></Link>
   <nav aria-label="Navigation" className="main-nav">
    <Link href="/observatorio/">{t("navObservatory")}</Link>
    <Link href="/comparar/">{locale==="pt"?"Comparar":locale==="es"?"Comparar":"Compare"}</Link>
    <Link href="/temas/">{t("navThemes")}</Link>
    <Link href="/territorios/">{t("navTerritories")}</Link>
    <Link href="/series/">{t("navTimeline")}</Link>
    <Link href="/analises/">{t("navAnalyses")}</Link>
    <Link href="/instituicoes/pesquisa/">{t("navInstitutions")}</Link>
    <Link href="/acervo/">{t("navCatalog")}</Link>
    <Link href="/indice-acesso/">{t("navAccess")}</Link>
    <Link href="/casos/">{t("navCases")}</Link>
    <Link href="/metodologia/">{t("navMethod")}</Link>
   </nav>
   <label className="locale-select"><span>{t("lang")}</span><select aria-label={t("changeLang")} value={locale} onChange={e=>setLocale(e.target.value as SiteLocale)}><option value="pt">PT</option><option value="en">EN</option><option value="es">ES</option></select></label>
  </div>
 </header>;
}
