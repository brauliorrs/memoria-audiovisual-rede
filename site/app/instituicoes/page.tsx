import type { Metadata } from "next";
import Link from "next/link";
import { institutions } from "@/lib/catalog";

export const metadata: Metadata = { title: "Instituições" };
export default function InstitutionsPage() {
  return <div className="shell page-shell">
    <p className="eyebrow">MAPEAMENTO INSTITUCIONAL</p>
    <h1>Instituições e corpora</h1>
    <p className="page-lede">Distinguir a existência de um conector técnico da autorização documental é parte central da governança do MAR. Apenas as fichas explicitamente publicadas entram na pesquisa. O inventário histórico de outras instituições, incluindo aquelas com restrição ou sem dados exibidos, está no Índice de Dados Públicos.</p>
    <p><Link href="/indice-acesso/">Consultar todos os corpora identificados e o índice de acesso ↗</Link></p>
    <div className="institution-grid">
      {institutions.map((item) => (
        <article className="institution-card" key={item.code}>
          <div className="institution-top"><span>{item.country}</span><span className={item.stage === "metadata" ? "state state-ready" : "state state-waiting"}>{item.stage === "metadata" ? "Metadados publicados" : "Em validação"}</span></div>
          <h2>{item.name}</h2>
          <p>{item.source}</p>
          <div className="institution-bottom"><span>{item.stage === "metadata" ? item.count + " fichas disponíveis" : "Sem fichas publicadas neste site"}</span>{item.stage === "metadata" && <Link href="/instituicoes/kavi/">Consultar ↗</Link>}</div>
        </article>
      ))}
    </div>
    <p className="disclaimer">Nota: a situação mostrada nesta página descreve a publicação no novo site experimental, não a totalidade de registros históricos do observatório nem uma autorização de coleta.</p>
  </div>;
}
