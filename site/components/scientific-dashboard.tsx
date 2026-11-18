"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { accessSummary, corpusList, formatNumber, groupByCategory, groupByTerritory } from "@/lib/scientific-observatory";

type View = "corpora" | "territory" | "category";
type Access = "all" | "public" | "restricted" | "without";

function Meter({ available, restricted }: { available: number; restricted: number }) {
  const total = available + restricted;
  if (!total) return <span className="ob-meter-empty">Sem volume quantificado</span>;
  return <div className="ob-meter" role="img" aria-label={`Superfície pública: ${formatNumber(available)}; restrita: ${formatNumber(restricted)}`}>
    <span className="ob-meter-public" style={{ width: `${100 * available / total}%` }} />
    <span className="ob-meter-restricted" style={{ width: `${100 * restricted / total}%` }} />
  </div>;
}

export function ScientificDashboard() {
  const [view, setView] = useState<View>("corpora");
  const [access, setAccess] = useState<Access>("all");
  const [continent, setContinent] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("total");

  const filtered = useMemo(() => corpusList.filter(item => {
    if (continent !== "all" && item.continent !== continent) return false;
    if (access === "public" && item.historicalPublicSurfaceRecords <= 0) return false;
    if (access === "restricted" && item.historicalRestrictedRecords <= 0) return false;
    if (access === "without" && item.historicalTotal > 0) return false;
    const terms = [item.name, item.code, item.shortLabel, item.category, item.continent].filter(Boolean).join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const q = query.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
    return !q || terms.includes(q);
  }), [access, continent, query]);

  const totals = useMemo(() => accessSummary(filtered), [filtered]);
  const table = useMemo(() => [...filtered].sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name, "pt-BR");
    if (sort === "restricted") return b.historicalRestrictedRecords - a.historicalRestrictedRecords;
    if (sort === "public") return b.historicalPublicSurfaceRecords - a.historicalPublicSurfaceRecords;
    return b.historicalTotal - a.historicalTotal;
  }), [filtered, sort]);
  const categories = useMemo(() => groupByCategory(filtered), [filtered]);
  const territories = useMemo(() => groupByTerritory(filtered), [filtered]);

  return <div className="ob-dashboard">
    <section className="ob-filter-panel" aria-label="Filtros da pesquisa científica">
      <div><label htmlFor="ob-query">Pesquisar corpus ou instituição</label><input id="ob-query" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Instituição, código ou categoria" /></div>
      <div><label htmlFor="ob-continent">Território</label><select id="ob-continent" value={continent} onChange={e => setContinent(e.target.value)}><option value="all">Todos</option><option value="Europe">Europa</option><option value="North America">América do Norte</option><option value="Nao classificado">Não classificado</option></select></div>
      <div><label htmlFor="ob-access">Evidência histórica</label><select id="ob-access" value={access} onChange={e => setAccess(e.target.value as Access)}><option value="all">Todos</option><option value="public">Superfície pública</option><option value="restricted">Registros restritos</option><option value="without">Sem volume materializado</option></select></div>
    </section>
    <section className="ob-kpis" aria-label="Indicadores para o recorte selecionado">
      <div><strong>{formatNumber(totals.units)}</strong><span>Corpora/unidades</span></div>
      <div><strong>{formatNumber(totals.withRecords)}</strong><span>Com registros históricos</span></div>
      <div><strong>{formatNumber(totals.publicSurface)}</strong><span>Classificados em superfície pública</span></div>
      <div><strong>{formatNumber(totals.restricted)}</strong><span>Classificados como restritos</span></div>
    </section>
    <div className="ob-viewbar">
      <div className="ob-viewtabs" role="group" aria-label="Visualização de dados">
        <button type="button" aria-pressed={view === "corpora"} onClick={() => setView("corpora")}>Corpora</button>
        <button type="button" aria-pressed={view === "territory"} onClick={() => setView("territory")}>Territórios</button>
        <button type="button" aria-pressed={view === "category"} onClick={() => setView("category")}>Categorias</button>
      </div>
      {view === "corpora" && <label className="ob-sort" htmlFor="ob-sort">Ordenar <select id="ob-sort" value={sort} onChange={e => setSort(e.target.value)}><option value="total">Total de registros</option><option value="public">Superfície pública</option><option value="restricted">Registros restritos</option><option value="name">Nome</option></select></label>}
    </div>
    {view === "corpora" ? <div className="ob-table-scroll"><table className="ob-table"><thead><tr><th>Corpus/instituição</th><th>Distribuição do acesso histórico</th><th>Público*</th><th>Restrito*</th><th>Estudar</th></tr></thead><tbody>{table.map(item => <tr key={item.code}><td><strong>{item.name}</strong><small>{item.shortLabel} · {item.category}</small></td><td><Meter available={item.historicalPublicSurfaceRecords} restricted={item.historicalRestrictedRecords}/></td><td>{formatNumber(item.historicalPublicSurfaceRecords)}</td><td>{formatNumber(item.historicalRestrictedRecords)}</td><td><Link href={`/observatorio/${item.code}/`}>Abrir análise</Link></td></tr>)}</tbody></table></div>
      : <div className="ob-group-list">{(view === "territory" ? territories : categories).map(item => <article key={item.name} className="ob-group"><div><h2>{item.name}</h2><p>{formatNumber(item.count)} corpora/unidades · {formatNumber(item.publicSurface + item.restricted)} registros</p></div><Meter available={item.publicSurface} restricted={item.restricted}/><p><strong>{formatNumber(item.publicSurface)}</strong> em superfície pública* · <strong>{formatNumber(item.restricted)}</strong> restritos*</p></article>)}</div>}
    <p className="disclaimer" role="note">* Classificações do índice histórico de junho de 2026, não disponibilidade atual e não autorização de publicação. Valores representam registros materializados, não o tamanho integral dos acervos. A pesquisa de fichas autorizadas permanece separada no <Link href="/acervo/">catálogo público</Link>.</p>
  </div>;
}
