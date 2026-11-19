import type { Metadata } from "next";
import Link from "next/link";
import {InstitutionalText} from "@/components/institutional-copy";
import {publicPageMetadata} from "@/lib/seo";
import { CatalogSearch } from "@/components/catalog-search";
import { publicIndex, records } from "@/lib/catalog";

export const metadata = publicPageMetadata("/instituicoes/kavi/","KAVI / Finna — catálogo de metadados","Índice parcial KAVI/Finna com fichas documentais autorizadas, SHA-256 de proveniência, reprodução e direitos não verificados.");
export default function KaviPage() {
  return <div className="shell page-shell">
    <Link href="/instituicoes/" className="back-link">← <InstitutionalText id="kaviBack"/></Link>
    <p className="eyebrow"><InstitutionalText id="kaviCountry"/></p>
    <h1>KAVI / Kuvi</h1>
    <p className="page-lede"><InstitutionalText id="kaviIntroStart"/> {publicIndex.total} <InstitutionalText id="kaviIntroEnd"/></p>
    <div className="notice"><strong><InstitutionalText id="kaviIntegrity"/></strong><p><InstitutionalText id="kaviWarning"/></p><small><InstitutionalText id="kaviObservation"/>: {publicIndex.observedOn} · <InstitutionalText id="kaviHash"/>: {publicIndex.catalogSha256}</small></div>
    <CatalogSearch items={records} />
  </div>;
}
