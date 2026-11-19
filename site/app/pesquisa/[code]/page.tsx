import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {historicalAnalyticReports} from "@/lib/historical-analytics";
import {dimensions,loadResearchData,researchSourceCodes,type ResearchDimension,type AnalyticRow} from "@/lib/research-dimensions";
import {ResearchExplorer} from "@/components/research-explorer";
import {InstitutionalText} from "@/components/institutional-i18n";

export function generateStaticParams(){return researchSourceCodes().map(code=>({code}));}
export async function generateMetadata({params}:{params:Promise<{code:string}>}):Promise<Metadata>{
 const {code}=await params;return {title:`Pesquisa temática — ${code.toUpperCase()} — MAR`};
}
export default async function ResearchSourcePage({params}:{params:Promise<{code:string}>}){
 const {code}=await params;
 const report=historicalAnalyticReports.find(x=>x.code===code);
 if(!report)notFound();
 const data=Object.fromEntries(dimensions.map(dim=>[dim,loadResearchData(code,dim)])) as Record<ResearchDimension,AnalyticRow[]>;
 return <main className="shell page-shell">
  <p className="eyebrow"><InstitutionalText id="researchEyebrow"/></p>
  <h1>{code.toUpperCase().replaceAll("_"," ")} — <InstitutionalText id="researchTitleSuffix"/></h1>
  <p className="page-lede"><InstitutionalText id="researchIntro"/></p>
  <p><Link href="/analises/"><InstitutionalText id="researchReports"/></Link> · <Link href="/observatorio/"><InstitutionalText id="researchObservatory"/></Link></p>
  <ResearchExplorer data={data}/>
  <p className="disclaimer"><InstitutionalText id="researchOrigin"/>: <code>data/output/{code}_*.csv</code>. <InstitutionalText id="researchFoot"/></p>
 </main>;
}
