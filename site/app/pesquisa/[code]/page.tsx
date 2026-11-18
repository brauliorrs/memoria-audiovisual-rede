import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {historicalAnalyticReports} from "@/lib/historical-analytics";
import {dimensions,loadResearchData,researchSourceCodes,type ResearchDimension,type AnalyticRow} from "@/lib/research-dimensions";
import {ResearchExplorer} from "@/components/research-explorer";
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
 <p className="eyebrow">OBSERVATÓRIO · INVESTIGAÇÃO COMPARADA</p>
 <h1>{code.toUpperCase().replaceAll("_"," ")} — temas, territórios e evolução</h1>
 <p className="page-lede">Explore os indicadores agregados gerados pelo Streamlit para esta fonte. Os dados são instantâneos de coleta e classificação documental, não autorização de reprodução audiovisual.</p>
 <p><Link href="/analises/">Comparar relatórios</Link> · <Link href="/observatorio/">Observatório</Link></p>
 <ResearchExplorer data={data}/>
 <p className="disclaimer">Origem: <code>data/output/{code}_*.csv</code>. A série de observações não deve ser confundida com cronologia histórica de filmes. A avaliação científica e os direitos de cada obra permanecem independentes.</p>
 </main>;
}
