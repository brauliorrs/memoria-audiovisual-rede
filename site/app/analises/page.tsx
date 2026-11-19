import {pageSeo} from "@/lib/seo";
import type {Metadata} from "next";
import Link from "next/link";
import {AnalyticsComparison} from "@/components/analytics-comparison";
import {historicalAnalyticReports} from "@/lib/historical-analytics";
import {ScientificText, ScientificNumber} from "@/components/scientific-i18n";

export const metadata=pageSeo("/analises/");
export default function AnalysesPage(){
 return <main className="shell page-shell">
  <p className="eyebrow"><ScientificText id="anEyebrow"/></p>
  <h1><ScientificText id="anTitle"/></h1>
  <p className="page-lede"><ScientificText id="anIntroStart"/> <ScientificNumber value={historicalAnalyticReports.length}/> <ScientificText id="anIntroAfter"/></p>
  <p><Link href="/comparar/"><ScientificText id="anCompare"/></Link> · <Link href="/observatorio/"><ScientificText id="anOverview"/></Link> · <Link href="/temas/"><ScientificText id="anThemes"/></Link> · <Link href="/series/"><ScientificText id="anTimeline"/></Link> · <Link href="/casos/"><ScientificText id="anCases"/></Link></p>
  <AnalyticsComparison/>
 </main>;
}
