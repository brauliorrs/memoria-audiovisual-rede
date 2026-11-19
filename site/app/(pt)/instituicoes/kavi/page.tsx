import {pageSeo} from "@/lib/seo";
import type {Metadata} from "next";
import Link from "@/components/site-link";
import {CatalogSearch} from "@/components/catalog-search";
import {InstitutionalText} from "@/components/institutional-i18n";
import {publicIndex,records} from "@/lib/catalog";

export const metadata=pageSeo("/instituicoes/kavi/");

export default function KaviPage(){
 return <div className="shell page-shell">
  <Link href="/instituicoes/" className="back-link">← <InstitutionalText id="kaviBack"/></Link>
  <p className="eyebrow"><InstitutionalText id="kaviEyebrow"/></p>
  <h1>KAVI / Kuvi</h1>
  <p className="page-lede"><InstitutionalText id="kaviIntroStart"/> {publicIndex.total} <InstitutionalText id="kaviIntroEnd"/></p>
  <div className="notice">
   <strong><InstitutionalText id="kaviNoticeTitle"/></strong>
   <p><InstitutionalText id="kaviNoticeBody"/></p>
   <small><InstitutionalText id="kaviObserved"/>: {publicIndex.observedOn} · <InstitutionalText id="kaviSha"/>: {publicIndex.catalogSha256}</small>
  </div>
  <CatalogSearch items={records}/>
 </div>;
}
