"use client";

import { useMemo, useState } from "react";
import inventory from "@/data/public-access-observatory.json";

type Corpus = (typeof inventory.corpora)[number];
type Filter = "all" | "historically-public" | "restricted" | "unquantified";

function displayReason(corpus: Corpus) {
  if (corpus.restrictionEvidence) return corpus.restrictionEvidence;
  if (corpus.historicalTotal === 0) return "Sem registros audiovisuais quantificados neste levantamento histórico. Acesso atual e possibilidade de publicação ainda não examinados.";
  return "A classificação histórica indica superfície pública de consulta, mas as fichas não foram liberadas para republicação no novo site. Direitos e acesso atual precisam de revisão por fonte.";
}

export function PublicAccessInventory() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const results = useMemo(() => inventory.corpora.filter((item) => {
    const q = query.trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const searchable = [item.name, item.shortLabel, item.code, item.accessCategory ?? "", item.continent].join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    if (q && !searchable.includes(q)) return false;
    if (filter === "historically-public") return item.historicalPublicSurfaceRecords > 0;
    if (filter === "restricted") return item.historicalRestrictedRecords > 0;
    if (filter === "unquantified") return item.historicalTotal === 0;
    return true;
  }), [query, filter]);

  return <section aria-label="Corpora mapeados e não exibidos">
    <div className="search-panel access-controls">
      <label htmlFor="access-search" className="search-label">Buscar corpus, instituição ou categoria</label>
      <input id="access-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ex.: Eye, Czech, Cinémathèque..." />
      <label className="filter-label" htmlFor="access-filter">Situação no levantamento histórico
        <select id="access-filter" value={filter} onChange={event => setFilter(event.target.value as Filter)}>
          <option value="all">Todos os corpora identificados</option>
          <option value="historically-public">Superfície pública observada</option>
          <option value="restricted">Registros classificados como restritos</option>
          <option value="unquantified">Sem volume materializado</option>
        </select>
      </label>
    </div>
    <p className="access-result-count" role="status">{results.length} corpora/unidades encontrados · publicação de fichas individuais ainda não liberada por este inventário</p>
    <div className="access-list">
      {results.map(item => <article className="access-entry" key={item.code}>
        <div className="access-entry-head"><div><p className="eyebrow">{item.continent === "Europe" ? "Europa" : item.continent === "North America" ? "América do Norte" : "Região não classificada"} · {item.code}</p><h2>{item.name}</h2></div>
        <span className="access-state">{item.historicalTotal === 0 ? "Identificado · sem volume quantificado" : "Identificado · fichas não exibidas"}</span></div>
        <p className="access-reason"><strong>Motivo da não exibição:</strong> {displayReason(item)}</p>
        <p className="access-reason"><strong>Acesso como visitante comum:</strong> {item.humanAccessNote} {item.sampleSourceUrl && <a href={item.sampleSourceUrl} target="_blank" rel="noopener noreferrer">Exemplo de ficha oficial ↗</a>}</p>
        <dl className="access-metrics">
          <div><dt>Registros em superfície pública*</dt><dd>{item.historicalPublicSurfaceRecords.toLocaleString("pt-BR")}</dd></div>
          <div><dt>Registros classificados como restritos*</dt><dd>{item.historicalRestrictedRecords.toLocaleString("pt-BR")}</dd></div>
          <div><dt>Fichas incorporadas por este inventário</dt><dd>0</dd></div>
        </dl>
        {item.accessCategory && <p className="access-category">Classificação histórica: {item.accessCategory}</p>}
      </article>)}
    </div>
    {results.length === 0 && <p>Nenhuma instituição corresponde à pesquisa.</p>}
    <p className="disclaimer">* Quantidades reproduzem o índice histórico do Streamlit (regra {inventory.observedRuleVersion}), não uma verificação atual ou total institucional. "Superfície pública" significa acesso observado no levantamento original, não autorização jurídica para republicar metadados. Restrições de mídia, autenticação e direitos são diferentes. Falha de ferramenta ou acesso não testado não significa ausência de catálogo. Nenhuma ficha nova é publicada por esta página.</p>
  </section>;
}
