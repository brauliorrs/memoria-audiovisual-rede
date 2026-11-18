import type {Metadata} from "next";
import Link from "next/link";
import {AnalyticsComparison} from "@/components/analytics-comparison";
import {historicalAnalyticReports} from "@/lib/historical-analytics";

export const metadata:Metadata={title:"Comparação de fontes e relatórios — MAR"};
export default function AnalysesPage(){
 return <main className="shell page-shell">
  <p className="eyebrow">OBSERVATÓRIO · PESQUISA COMPARADA</p>
  <h1>Indicadores e relatórios por fonte</h1>
  <p className="page-lede">Explore os {historicalAnalyticReports.length} relatórios analíticos consolidados pela pesquisa original do Streamlit: instituições, sites, plataformas e evidências documentais. Compare fontes sem confundir volume coletado com cobertura integral dos arquivos.</p>
  <p><Link href="/comparar/">Comparar fontes em uma investigação ↗</Link> · <Link href="/observatorio/">Visão integrada do observatório</Link> · <Link href="/temas/">Temas e territórios</Link> · <Link href="/series/">Séries temporais</Link> · <Link href="/casos/">Casos documentados</Link></p>
  <AnalyticsComparison/>
 </main>;
}
