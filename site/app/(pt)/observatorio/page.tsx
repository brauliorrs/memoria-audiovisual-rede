import {pageSeo} from "@/lib/seo";
import type { Metadata } from "next";
import Link from "@/components/site-link";
import { ScientificDashboard } from "@/components/scientific-dashboard";
import { historicalSnapshot } from "@/lib/scientific-observatory";
import {ScientificText, ScientificNumber} from "@/components/scientific-i18n";

export const metadata=pageSeo("/observatorio/");

export default function ObservatoryPage() {
  return <main className="shell page-shell">
    <p className="eyebrow"><ScientificText id="obEyebrow"/></p>
    <h1><ScientificText id="obTitle"/></h1>
    <p className="page-lede"><ScientificText id="obIntro"/></p>
    <div className="access-explainer">
      <p><strong><ScientificText id="obSnapshotLead"/></strong> <ScientificNumber value={historicalSnapshot.summary.historicalMaterializedTotal}/> <ScientificText id="obSnapshotAfter"/></p>
      <p><strong><ScientificText id="obLayersLead"/></strong> <ScientificText id="obLayers"/> <Link href="/acervo/"><ScientificText id="obCatalogLink"/></Link> <ScientificText id="obCatalogAfter"/></p>
    </div>
    <p><Link href="/territorios/"><ScientificText id="obGoMap"/></Link> · <Link href="/comparar/"><ScientificText id="obGoCompare"/></Link> · <Link href="/temas/"><ScientificText id="obGoThemes"/></Link> · <Link href="/series/"><ScientificText id="obGoTimeline"/></Link> · <Link href="/instituicoes/pesquisa/"><ScientificText id="obGoInstitutions"/></Link></p>
    <ScientificDashboard/>
  </main>;
}
