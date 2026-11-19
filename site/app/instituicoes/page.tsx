import type { Metadata } from "next";
import Link from "next/link";
import {InstitutionalText} from "@/components/institutional-copy";
import {publicPageMetadata} from "@/lib/seo";
import { institutions } from "@/lib/catalog";

export const metadata = publicPageMetadata("/instituicoes/","Instituições e corpora","Inventário institucional audiovisual com estados de validação e limites de publicação dos metadados no MAR.");
export default function InstitutionsPage() {
  return <div className="shell page-shell">
    <p className="eyebrow"><InstitutionalText id="institutionEyebrow"/></p>
    <h1><InstitutionalText id="institutionTitle"/></h1>
    <p className="page-lede"><InstitutionalText id="institutionIntro"/></p>
    <p><Link href="/instituicoes/pesquisa/"><InstitutionalText id="institutionResearch"/> ↗</Link> · <Link href="/indice-acesso/"><InstitutionalText id="institutionAccess"/> ↗</Link></p>
    <div className="institution-grid">
      {institutions.map((item) => (
        <article className="institution-card" key={item.code}>
          <div className="institution-top"><span>{item.country}</span><span className={item.stage === "metadata" ? "state state-ready" : "state state-waiting"}><InstitutionalText id={item.stage === "metadata" ? "institutionPublished" : "institutionValidation"}/></span></div>
          <h2>{item.name}</h2>
          <p>{item.stage === "metadata" ? item.source : <InstitutionalText id="institutionTechnical"/>}</p>
          <div className="institution-bottom"><span>{item.stage === "metadata" ? <>{item.count} <InstitutionalText id="institutionAvailable"/></> : <InstitutionalText id="institutionUnpublished"/>}</span>{item.stage === "metadata" && <Link href="/instituicoes/kavi/"><InstitutionalText id="institutionView"/> ↗</Link>}</div>
        </article>
      ))}
    </div>
    <p className="disclaimer"><InstitutionalText id="institutionNotice"/></p>
  </div>;
}
