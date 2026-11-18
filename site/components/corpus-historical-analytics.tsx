import Link from "next/link";
import { formatNumber } from "@/lib/scientific-observatory";
import { type HistoricalAnalyticReport, rankSummary } from "@/lib/historical-analytics";

function Distribution({title, values}: {title:string, values:Record<string,number>}) {
  const entries=rankSummary(values,10);
  if (!entries.length) return null;
  const max=Math.max(...entries.map(([,number])=>number),1);
  return <div className="ob-panel">
    <h3>{title}</h3>
    <div className="ob-bars">{entries.map(([label,value])=><div className="ob-bar-item" key={label}>
      <div className="ob-bar-label"><span>{label.replaceAll("_"," ")}</span><strong>{formatNumber(value)}</strong></div>
      <div className="ob-bar-track"><span style={{width:`${100*value/max}%`}}/></div>
    </div>)}</div>
  </div>;
}

export function CorpusHistoricalAnalytics({report}:{report:HistoricalAnalyticReport}) {
  return <section className="ob-analytic-section" aria-label="Indicadores analíticos históricos">
    <p className="eyebrow">ANÁLISE DA FONTE · RELATÓRIO HISTÓRICO</p>
    <h2>Instituições, plataformas e condições de acesso</h2>
    <p>Indicadores agregados migrados da análise já existente no Streamlit. Os totais referem-se à cobertura do relatório da fonte, não ao conjunto completo do patrimônio audiovisual da instituição.</p>
    <div className="ob-kpis">
      <div><strong>{formatNumber(report.totalInstitutions)}</strong><span>Instituições na análise</span></div>
      <div><strong>{formatNumber(report.institutionsWithVideo)}</strong><span>Instituições com sinal de vídeo</span></div>
      <div><strong>{formatNumber(report.withEmbeds)}</strong><span>Instituições com indicador de incorporação</span></div>
      <div><strong>{formatNumber(Object.values(report.platforms).reduce((a,b)=>a+b,0))}</strong><span>Ocorrências por plataforma*</span></div>
    </div>
    <div className="ob-group-list">
      <Distribution title="Situação dos sites institucionais" values={report.siteStatus}/>
      <Distribution title="Integridade observada" values={report.integrity}/>
      <Distribution title="Plataformas identificadas" values={report.platforms}/>
      <Distribution title="Instituições por continente" values={report.continents}/>
    </div>
    <p className="disclaimer">* Indicadores históricos do relatório <code>{report.source}</code>. Uma ocorrência de plataforma, incorporação ou link não comprova reprodução pública, direitos de uso ou licença para publicar uma ficha individual.</p>
    <p><Link href="/analises/">Comparar todos os relatórios históricos →</Link></p>
  </section>;
}
