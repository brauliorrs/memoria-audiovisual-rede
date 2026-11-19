import {pageSeo} from "@/lib/seo";
import type {Metadata} from "next";
import {DocumentedCases} from "@/components/documented-cases";
import {ScientificText,ScientificNumber} from "@/components/scientific-i18n";
import cases from "@/data/documented-cases.json";
export const metadata=pageSeo("/casos/");
export default function CasesPage(){return <main className="shell page-shell">
  <p className="eyebrow"><ScientificText id="casesEyebrow"/></p>
  <h1><ScientificText id="casesTitle"/></h1>
  <p className="page-lede"><ScientificText id="casesIntroLead"/> <ScientificNumber value={cases.cases.length}/> <ScientificText id="casesIntroEnd"/></p>
  <DocumentedCases/>
</main>;}
