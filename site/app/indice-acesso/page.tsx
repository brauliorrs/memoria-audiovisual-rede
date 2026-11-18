import type { Metadata } from "next";
import Link from "next/link";
import { PublicAccessInventory } from "@/components/public-access-inventory";
import inventory from "@/data/public-access-observatory.json";

export const metadata: Metadata = { title: "Índice de Dados Públicos e corpora não exibidos" };

export default function AccessIndexPage() {
  const summary = inventory.summary;
  return <main className="shell page-shell">
    <p className="eyebrow">OBSERVATÓRIO · TRANSPARÊNCIA DO ACESSO</p>
    <h1>Índice de Dados Públicos</h1>
    <p className="page-lede">Inventário histórico dos corpora identificados pelo MAR, inclusive os que não têm fichas publicadas no novo site. Quando não é possível exibir um conjunto, preservamos sua existência e explicamos a limitação conhecida, sem afirmar que a instituição não disponibiliza o acervo.</p>
    <div className="access-explainer">
      <p><strong>O que este índice mede:</strong> o levantamento histórico do Streamlit classificou {summary.historicalMaterializedTotal.toLocaleString("pt-BR")} registros materializados, dos quais {summary.historicalPublicSurfaceRecords.toLocaleString("pt-BR")} em superfícies públicas e {summary.historicalRestrictedRecords.toLocaleString("pt-BR")} em superfícies restritas. Esses números são históricos, não medem permissão de republicação nem disponibilidade em tempo real.</p>
      <p><strong>O que está publicado:</strong> somente as {inventory.kaviSiteApprovedRecords} fichas KAVI/Finna já aprovadas, disponíveis no <Link href="/acervo/">catálogo público</Link>. Os demais corpora apresentados abaixo constam do inventário de acesso, não da pesquisa de fichas.</p>
      <p><strong>Por que algumas fichas não aparecem:</strong> a reutilização pode depender de licença, autorização, revisão científica, termos do serviço ou acesso técnico. Se não há evidência suficiente para atribuir uma razão específica, indicamos “a confirmar”; nunca classificamos como ilegal sem fundamento.</p>
    </div>
    <PublicAccessInventory />
  </main>;
}
