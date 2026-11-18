import type { Metadata } from "next";
import Link from "next/link";
import { ScientificDashboard } from "@/components/scientific-dashboard";
import { historicalSnapshot } from "@/lib/scientific-observatory";

export const metadata: Metadata = { title: "Observatório científico — análises e corpora" };

export default function ObservatoryPage() {
  return <main className="shell page-shell">
    <p className="eyebrow">PESQUISA CIENTÍFICA · AUDIOVISUAL EM REDE</p>
    <h1>Observatório de memória audiovisual</h1>
    <p className="page-lede">Investigue a distribuição documental dos acervos identificados, compare instituições e territórios, e examine limites de acesso. Esta é a transposição dos painéis analíticos do Streamlit para o MAR no Vercel.</p>
    <div className="access-explainer"><p><strong>Leitura dos indicadores:</strong> o levantamento histórico contém {new Intl.NumberFormat("pt-BR").format(historicalSnapshot.summary.historicalMaterializedTotal)} registros materializados. Trata-se de um recorte de pesquisa, não do tamanho total dos acervos e nem da quantidade de fichas autorizadas para reprodução.</p><p><strong>Três camadas independentes:</strong> acervo identificado, registros consultáveis na origem e fichas autorizadas para publicação no MAR. A pesquisa científica usa as contagens e estados históricos; a <Link href="/acervo/">pesquisa de fichas</Link> mostra apenas as 200 KAVI aprovadas.</p></div>
    <ScientificDashboard/>
  </main>;
}
