import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { corpusList, getHistoricalCorpus } from "@/lib/scientific-observatory";
import {ScientificText,ScientificNumber,ScientificPercent,ScientificTerritory} from "@/components/scientific-i18n";
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

  return <main className="shell page-shell">
    <nav className="ob-breadcrumb" aria-label="Breadcrumb"><Link href="/observatorio/"><ScientificText id="profBreadcrumb"/></Link><span aria-hidden="true">/</span><span>{corpus.shortLabel}</span></nav>
    <p className="eyebrow"><ScientificText id="profEyebrow"/></p>
    <h1>{corpus.name}</h1>
    <p className="page-lede"><ScientificText id="profIntro"/></p>
    <div className="ob-profile-tags"><span>{corpus.category}</span><span><ScientificTerritory value={corpus.continent||"Nao classificado"}/></span><span><ScientificText id="profIdentifier"/>: {corpus.code}</span></div>
    <div className="ob-kpis">
      <div><strong><ScientificNumber value={corpus.historicalTotal}/></strong><span><ScientificText id="profMaterialized"/></span></div>
      <div><strong><ScientificNumber value={corpus.historicalPublicSurfaceRecords}/></strong><span><ScientificText id="profPublic"/></span></div>
      <div><strong><ScientificNumber value={corpus.historicalRestrictedRecords}/></strong><span><ScientificText id="profRestricted"/></span></div>
      <div><strong><ScientificPercent part={corpus.historicalPublicSurfaceRecords} total={corpus.historicalTotal}/></strong><span><ScientificText id="profFraction"/></span></div>
    </div>
    <section className="ob-profile-columns">
      <article className="ob-panel">
        <h2><ScientificText id="profAccess"/></h2>
        <p className="disclaimer"><ScientificText id="profSourceText"/></p><p>{corpus.humanAccessNote}</p>
        {corpus.sampleSourceUrl && <p><a href={corpus.sampleSourceUrl} rel="noopener noreferrer" target="_blank"><ScientificText id="profInstitutionalSource"/></a></p>}
        <p><strong><ScientificText id="profEvidence"/>:</strong> {corpus.humanAccessEvidence.replaceAll("_", " ")}</p>
      </article>
      <article className="ob-panel">
        <h2><ScientificText id="profVisibility"/></h2>
        <p>{corpus.reviewReason}</p>
        {corpus.restrictionEvidence && <p><strong><ScientificText id="profHistoricalRestriction"/>:</strong> {corpus.restrictionEvidence}</p>}
        {corpus.rightsPolicyUrl && <p><a href={corpus.rightsPolicyUrl} target="_blank" rel="noopener noreferrer"><ScientificText id="profRights"/></a></p>}
        <p><strong><ScientificText id="profIndividual"/>:</strong> <ScientificText id="profNotReleased"/></p>
      </article>
    </section>
    {report && <CorpusHistoricalAnalytics report={report}/>}
    {getResearchSlice(code) && <CorpusResearchSections code={code}/>}
    {getInstitutionGroup(code) && <p><Link href="/instituicoes/pesquisa/"><ScientificText id="profInstitutionBrowse"/></Link></p>}
    <section className="ob-panel">
      <h2><ScientificText id="profResearchTitle"/></h2>
      <p><ScientificText id="profResearchQuestion"/></p>
      <p><Link href="/indice-acesso/"><ScientificText id="profAccessIndex"/></Link> · <Link href="/metodologia/"><ScientificText id="profMethodology"/></Link></p>
    </section>
    <p className="disclaimer">* <ScientificText id="profFootnote"/></p>
  </main>;
}
