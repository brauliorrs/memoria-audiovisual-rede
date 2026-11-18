import type { Metadata } from "next";
import { CatalogSearch } from "@/components/catalog-search";
import { publicIndex, records } from "@/lib/catalog";
import {ScientificText,ScientificNumber} from "@/components/scientific-i18n";

export const metadata: Metadata = { title: "Catálogo público" };
export default function AcervoPage() {
  return <div className="shell page-shell">
    <p className="eyebrow"><ScientificText id="catalogEyebrow"/></p>
    <h1><ScientificText id="catalogTitle"/></h1>
    <p className="page-lede"><ScientificText id="catalogIntroLead"/> <ScientificNumber value={publicIndex.total}/> <ScientificText id="catalogIntroEnd"/></p>
    <CatalogSearch items={records} />
  </div>;
}
