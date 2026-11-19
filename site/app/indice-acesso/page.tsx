import type { Metadata } from "next";
import Link from "next/link";
import {PublicAccessInventory} from "@/components/public-access-inventory";
import {ScientificText,ScientificNumber} from "@/components/scientific-i18n";
import inventory from "@/data/public-access-observatory.json";

export const metadata: Metadata = {title:"Índice de Dados Públicos e corpora não exibidos"};

export default function AccessIndexPage(){
 const summary=inventory.summary;
 return <main className="shell page-shell">
  <p className="eyebrow"><ScientificText id="accessEyebrow"/></p>
  <h1><ScientificText id="accessTitle"/></h1>
  <p className="page-lede"><ScientificText id="accessIntro"/></p>
  <div className="access-explainer">
   <p><strong><ScientificText id="accessMeasureLead"/></strong>{" "}
    <ScientificText id="accessMeasureFirst"/>{" "}
    <ScientificNumber value={summary.historicalMaterializedTotal}/>{" "}
    <ScientificText id="accessMeasureMaterialized"/>{" "}
    <ScientificNumber value={summary.historicalPublicSurfaceRecords}/>{" "}
    <ScientificText id="accessMeasurePublic"/>{" "}
    <ScientificNumber value={summary.historicalRestrictedRecords}/>{" "}
    <ScientificText id="accessMeasureRestricted"/></p>
   <p><strong><ScientificText id="accessPublishedLead"/></strong>{" "}
    <ScientificText id="accessPublishedFirst"/>{" "}
    <ScientificNumber value={inventory.kaviSiteApprovedRecords}/>{" "}
    <ScientificText id="accessPublishedMiddle"/>{" "}
    <Link href="/acervo/"><ScientificText id="accessCatalogLink"/></Link>.{" "}
    <ScientificText id="accessPublishedAfter"/></p>
   <p><strong><ScientificText id="accessWhyLead"/></strong>{" "}
    <ScientificText id="accessWhyBody"/></p>
  </div>
  <PublicAccessInventory/>
 </main>;
}
