import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { corpusList, formatNumber, getHistoricalCorpus } from "@/lib/scientific-observatory";
import { getAnalyticReport } from "@/lib/historical-analytics";
import { CorpusHistoricalAnalytics } from "@/components/corpus-historical-analytics";
import {CorpusResearchSections} from "@/components/corpus-research-sections";
import {getResearchSlice} from "@/lib/research-slices";
import {getInstitutionGroup} from "@/lib/institutional-profiles";

export function generateStaticParams() {
  return corpusList.map(item => ({ code: item.code }));
}

export async function generateMetadata({ params }: { params: Promise<{ code: string }> }): Promise<Metadata> {
  const { code } = await params;
  const corpus = getHistoricalCorpus(code);
  return { title: corpus ? `Análise documental — ${corpus.name}` : "Corpus não identificado" };
}

export default async function CorpusAnalysisPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const corpus = getHistoricalCorpus(code);
  if (!corpus) notFound();
  const report = getAnalyticReport(code);
  const percent = corpus.historicalTotal ? (100 * corpus.historicalPublicSurfaceRecords / corpus.historicalTotal).toFixed(1) : null;

  return <main className="shell page-shell">
    <nav className="ob-breadcrumb" aria-label="Localização"><Link href="/observatorio/">Observatório</Link><span aria-hidden="true">/</span><span>{corpus.shortLabel}</span></nav>
    <p className="eyebrow">FICHA DE ESTUDO · INSTITUIÇÃO / CORPUS</p>
    <h1>{corpus.name}</h1>
    <p className="page-lede">Perfil de análise documental histórica. A existência de registros no inventário não representa autorização de republicação de metadados ou acesso audiovisual integral.</p>
    <div className="ob-profile-tags"><span>{corpus.category}</span><span>{corpus.continent === "Europe" ? "Europa" : corpus.continent === "North America" ? "América do Norte" : "Localização não classificada"}</span><span>Identificador: {corpus.code}</span></div>
    <div className="ob-kpis">
      <div><strong>{formatNumber(corpus.historicalTotal)}</strong><span>Registros materializados*</span></div>
      <div><strong>{formatNumber(corpus.historicalPublicSurfaceRecords)}</strong><span>Superfície pública*</span></div>
      <div><strong>{formatNumber(corpus.historicalRestrictedRecords)}</strong><span>Classificação restrita*</span></div>
      <div><strong>{percent === null ? "—" : percent + "%"}</strong><span>Fração pública do recorte*</span></div>
    </div>
    <section className="ob-profile-columns">
      <article className="ob-panel">
        <h2>Acesso e consulta como visitante</h2>
        <p>{corpus.humanAccessNote}</p>
        {corpus.sampleSourceUrl && <p><a href={corpus.sampleSourceUrl} rel="noopener noreferrer" target="_blank">Consultar a rota institucional ↗</a></p>}
        <p><strong>Estado documental:</strong> {corpus.humanAccessEvidence.replaceAll("_", " ")}</p>
      </article>
      <article className="ob-panel">
        <h2>Visibilidade e limites de reutilização</h2>
        <p>{corpus.reviewReason}</p>
        {corpus.restrictionEvidence && <p><strong>Restrição histórica:</strong> {corpus.restrictionEvidence}</p>}
        {corpus.rightsPolicyUrl && <p><a href={corpus.rightsPolicyUrl} target="_blank" rel="noopener noreferrer">Examinar a política da fonte ↗</a></p>}
        <p><strong>Publicação individual:</strong> fichas não liberadas por este inventário.</p>
      </article>
    </section>
    {report && <CorpusHistoricalAnalytics report={report}/>}
    {getResearchSlice(code) && <CorpusResearchSections code={code}/>}
    {getInstitutionGroup(code) && <p><Link href="/instituicoes/pesquisa/">Consultar fichas institucionais de pesquisa ↗</Link></p>}
    <section className="ob-panel">
      <h2>Questões de pesquisa para este corpus</h2>
      <p>Em que extensão os registros são documentados publicamente? Como os regimes de acesso afetam a visibilidade histórica? Qual a relação entre o acervo identificado, os metadados em superfície pública e o patrimônio audiovisual efetivamente consultável? O MAR preserva a distinção entre evidência e inferência para orientar a investigação.</p>
      <p><Link href="/indice-acesso/">Consultar Índice de Dados Públicos</Link> · <Link href="/metodologia/">Metodologia de pesquisa</Link></p>
    </section>
    <p className="disclaimer">* Dados históricos do Observatório (junho de 2026). O denominador considera somente registros materializados nesse snapshot. Não houve nova validação individual de mídia nem liberação de fichas ao criar esta página. Verificação de direitos e revisão científica permanecem específicas por fonte.</p>
  </main>;
}
