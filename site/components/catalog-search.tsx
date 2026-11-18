"use client";
import { useMemo, useState } from "react";
import type { RecordItem } from "@/lib/catalog";

function fold(text: string) {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
}

export function CatalogSearch({ items }: { items: RecordItem[] }) {
  const [term, setTerm] = useState("");
  const [year, setYear] = useState("all");
  const [limit, setLimit] = useState(18);
  const decades = useMemo(() => Array.from(
    new Set(items.map((i) => i.year && /^\d{4}$/.test(i.year) ? Math.floor(Number(i.year) / 10) * 10 : null).filter((n): n is number => n !== null)),
  ).sort((a, b) => a - b), [items]);
  const matches = useMemo(() => {
    const query = fold(term.trim());
    return items.filter((i) => {
      const searchable = fold([i.title, i.subjects, i.genres, i.id, i.year ?? "", i.institution].join(" "));
      if (query && !searchable.includes(query)) return false;
      if (year !== "all" && Math.floor(Number(i.year) / 10) * 10 !== Number(year)) return false;
      return true;
    });
  }, [term, year, items]);
  const visible = matches.slice(0, limit);

  return (
    <section className="search-module" aria-label="Pesquisa no acervo">
      <div className="search-panel">
        <label className="search-label" htmlFor="mar-search">Pesquisar por título, tema ou identificador</label>
        <div className="search-fields">
          <div className="search-input-wrap">
            <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
            <input
              id="mar-search"
              value={term}
              onChange={(event) => { setTerm(event.target.value); setLimit(18); }}
              placeholder="Ex.: cinema finlandês, Pojat, 1962..."
              autoComplete="off"
            />
          </div>
          <label className="filter-label" htmlFor="mar-decade">
            Período
            <select id="mar-decade" value={year} onChange={(event) => { setYear(event.target.value); setLimit(18); }}>
              <option value="all">Todos os períodos</option>
              {decades.map((d) => <option value={String(d)} key={d}>{d}–{d + 9}</option>)}
            </select>
          </label>
        </div>
        <p className="search-helper">Fonte selecionada: <strong>KAVI / Kuvi · Finna</strong> <span aria-hidden="true">·</span> Situação: <strong>metadados publicados, cobertura parcial</strong></p>
      </div>
      <div className="results-head">
        <div>
          <p className="eyebrow">REGISTROS DOCUMENTAIS</p>
          <h2>{matches.length} {matches.length === 1 ? "ficha encontrada" : "fichas encontradas"}</h2>
        </div>
        <span className="results-chip">Reprodução não verificada</span>
      </div>
      {visible.length === 0 ? (
        <div className="empty-state">
          <strong>Nenhuma ficha corresponde à pesquisa.</strong>
          <p>Tente outro termo ou selecione todos os períodos.</p>
          <button className="text-button" onClick={() => { setTerm(""); setYear("all"); }}>Limpar filtros</button>
        </div>
      ) : (
        <div className="record-grid">
          {visible.map((item) => (
            <article className="record-card" key={item.id}>
              <div className="record-meta"><span>KAVI / FINNA</span><span>{item.year ?? "Ano não informado"}</span></div>
              <div className="record-icon" aria-hidden="true">▣</div>
              <h3>{item.title}</h3>
              <p className="record-subject">{item.genres || item.subjects || "Assuntos não informados no registro."}</p>
              <p className="record-id">{item.id}</p>
              <div className="record-footer">
                <span className="record-status">Ficha de origem</span>
                <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" aria-label={"Abrir ficha original de " + item.title}>Ver ficha ↗</a>
              </div>
            </article>
          ))}
        </div>
      )}
      {matches.length > visible.length && <div className="load-more"><button type="button" onClick={() => setLimit((n) => n + 18)}>Mostrar mais fichas <span>({matches.length - visible.length} restantes)</span></button></div>}
    </section>
  );
}
