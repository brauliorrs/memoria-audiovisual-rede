"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import type { RecordItem } from "@/lib/catalog";

const PAGE_SIZE = 18;
function fold(text: string) {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
}
function yearOf(item: RecordItem): number | null {
  return item.year && /^\d{4}$/.test(item.year) ? Number(item.year) : null;
}
function topicsOf(item: RecordItem): string[] {
  return [...item.genres.split(";"), ...item.subjects.split(";")].map((value) => value.trim()).filter(Boolean);
}

export function CatalogSearch({ items }: { items: RecordItem[] }) {
  const [term, setTerm] = useState("");
  const [decade, setDecade] = useState("all");
  const [topic, setTopic] = useState("all");
  const [order, setOrder] = useState("title");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const decades = useMemo(() => Array.from(new Set(items
    .map((item) => yearOf(item))
    .filter((year): year is number => year !== null)
    .map((year) => Math.floor(year / 10) * 10),
  )).sort((a, b) => a - b), [items]);
  const topics = useMemo(() => [...new Set(items.flatMap(topicsOf))]
    .sort((a, b) => a.localeCompare(b, "pt-BR")), [items]);

  const matches = useMemo(() => {
    const query = fold(term.trim());
    const matched = items.filter((item) => {
      const searchable = fold([item.title, item.subjects, item.genres, item.id, item.year ?? "", item.institution, item.country, item.source].join(" "));
      if (query && !searchable.includes(query)) return false;
      const year = yearOf(item);
      if (decade !== "all" && (year === null || Math.floor(year / 10) * 10 !== Number(decade))) return false;
      if (topic !== "all" && !topicsOf(item).includes(topic)) return false;
      return true;
    });
    return matched.sort((a, b) => {
      const aYear = yearOf(a);
      const bYear = yearOf(b);
      if (order === "newest") return (bYear ?? -Infinity) - (aYear ?? -Infinity) || a.title.localeCompare(b.title, "pt-BR");
      if (order === "oldest") return (aYear ?? Infinity) - (bYear ?? Infinity) || a.title.localeCompare(b.title, "pt-BR");
      return a.title.localeCompare(b.title, "pt-BR") || a.id.localeCompare(b.id);
    });
  }, [items, term, decade, topic, order]);
  const visible = matches.slice(0, limit);
  function reset() {
    setTerm("");
    setDecade("all");
    setTopic("all");
    setOrder("title");
    setLimit(PAGE_SIZE);
  }

  return (
    <section className="search-module" aria-label="Pesquisa no acervo">
      <div className="search-panel">
        <label className="search-label" htmlFor="mar-search">Pesquisar por título, assunto, instituição ou identificador</label>
        <div className="search-fields search-fields-advanced">
          <div className="search-input-wrap">
            <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
            <input
              id="mar-search"
              type="search"
              value={term}
              onChange={(event) => { setTerm(event.target.value); setLimit(PAGE_SIZE); }}
              placeholder="Ex.: Pojat, 1962, documentário..."
              autoComplete="off"
            />
          </div>
          <label className="filter-label" htmlFor="mar-decade">
            Período
            <select id="mar-decade" value={decade} onChange={(event) => { setDecade(event.target.value); setLimit(PAGE_SIZE); }}>
              <option value="all">Todos os períodos</option>
              {decades.map((value) => <option value={String(value)} key={value}>{value}–{value + 9}</option>)}
            </select>
          </label>
          <label className="filter-label" htmlFor="mar-topic">
            Tema / gênero
            <select id="mar-topic" value={topic} onChange={(event) => { setTopic(event.target.value); setLimit(PAGE_SIZE); }}>
              <option value="all">Todos os temas</option>
              {topics.map((value) => <option value={value} key={value}>{value}</option>)}
            </select>
          </label>
          <label className="filter-label" htmlFor="mar-order">
            Ordenação
            <select id="mar-order" value={order} onChange={(event) => { setOrder(event.target.value); setLimit(PAGE_SIZE); }}>
              <option value="title">Título (A–Z)</option>
              <option value="newest">Ano (mais recente)</option>
              <option value="oldest">Ano (mais antigo)</option>
            </select>
          </label>
        </div>
        <div className="search-hints">
          <p className="search-helper">Acervo publicado: <strong>KAVI / Kuvi · Finna</strong> <span aria-hidden="true">·</span> <strong>cobertura parcial</strong>, mídia não verificada.</p>
          <button type="button" className="text-button" onClick={reset}>Limpar filtros</button>
        </div>
      </div>
      <div className="results-head" role="status" aria-live="polite">
        <div>
          <p className="eyebrow">REGISTROS DOCUMENTAIS</p>
          <h2>{matches.length} {matches.length === 1 ? "ficha encontrada" : "fichas encontradas"}</h2>
        </div>
        <span className="results-chip">Metadados · reprodução não verificada</span>
      </div>
      {visible.length === 0 ? (
        <div className="empty-state">
          <strong>Nenhuma ficha corresponde aos filtros.</strong>
          <p>Experimente outro termo, período ou tema.</p>
          <button type="button" className="text-button" onClick={reset}>Limpar pesquisa e filtros</button>
        </div>
      ) : (
        <div className="record-grid">
          {visible.map((item) => (
            <article className="record-card" key={item.id}>
              <div className="record-meta"><span>KAVI / FINNA</span><span>{item.year ?? "Ano não informado"}</span></div>
              <div className="record-icon" aria-hidden="true">▣</div>
              <h3><Link href={"/acervo/kavi/" + encodeURIComponent(item.id) + "/"}>{item.title}</Link></h3>
              <p className="record-subject">{item.genres || item.subjects || "Assuntos não informados no registro."}</p>
              <p className="record-id">{item.id}</p>
              <div className="record-footer">
                <span className="record-status">Ficha documental</span>
                <Link href={"/acervo/kavi/" + encodeURIComponent(item.id) + "/"} aria-label={"Ver ficha documental de " + item.title}>Consultar ficha ↗</Link>
              </div>
            </article>
          ))}
        </div>
      )}
      {matches.length > visible.length && (
        <div className="load-more">
          <button type="button" onClick={() => setLimit((value) => value + PAGE_SIZE)}>
            Mostrar mais fichas <span>({matches.length - visible.length} restantes)</span>
          </button>
        </div>
      )}
    </section>
  );
}
