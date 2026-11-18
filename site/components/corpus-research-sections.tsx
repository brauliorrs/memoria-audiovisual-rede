"use client";
import {useState} from "react";
import {ResearchWorkbench} from "@/components/research-workbench";
import {useSiteLocale} from "@/components/site-locale";

export function CorpusResearchSections({code}:{code:string}){
 const [view,setView]=useState<"themes"|"timeline">("themes");
 const {t}=useSiteLocale();
 return <section className="corpus-research-sections" aria-label="Source analysis">
  <div className="ob-viewtabs" role="group" aria-label={t("navAnalyses")}><button type="button" aria-pressed={view==="themes"} onClick={()=>setView("themes")}>{t("navThemes")}</button><button type="button" aria-pressed={view==="timeline"} onClick={()=>setView("timeline")}>{t("navTimeline")}</button></div>
  <ResearchWorkbench mode={view} initialCorpus={code}/>
 </section>;
}
