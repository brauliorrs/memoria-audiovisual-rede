"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import type { RecordItem } from "@/lib/catalog";
import {useScientificCopy} from "@/components/scientific-i18n";
import {useSiteLocale} from "@/components/site-locale";

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
  const copy=useScientificCopy();
  const {locale}=useSiteLocale();
  const format=(value:number)=>new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US").format(value);
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
    <section className="search-module" aria-label={copy.catalogSearchSection}>
      <div className="search-panel">
        <label className="search-label" htmlFor="mar-search">{copy.catalogSearchLabel}</label>
        <div className="search-fields search-fields-advanced">
          <div className="search-input-wrap">
            <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
            <input
              id="mar-search"
              type="search"
              value={term}
              onChange={(event) => { setTerm(event.target.value); setLimit(PAGE_SIZE); }}
              placeholder={copy.catalogSearchPlaceholder}
              autoComplete="off"
            />
          </div>
          <label className="filter-label" htmlFor="mar-decade">
            {copy.catalogPeriod}
            <select id="mar-decade" value={decade} onChange={(event) => { setDecade(event.target.value); setLimit(PAGE_SIZE); }}>
              <option value="all">{copy.catalogAllPeriods}</option>
              {decades.map((value) => <option value={String(value)} key={value}>{value}–{value + 9}</option>)}
            </select>
          </label>
          <label className="filter-label" htmlFor="mar-topic">
            {copy.catalogTopicGenre}
            <select id="mar-topic" value={topic} onChange={(event) => { setTopic(event.target.value); setLimit(PAGE_SIZE); }}>
              <option value="all">{copy.catalogAllTopics}</option>
              {topics.map((value) => <option value={value} key={value}>{value}</option>)}
            </select>
          </label>
          <label className="filter-label" htmlFor="mar-order">
            {copy.catalogSort}
            <select id="mar-order" value={order} onChange={(event) => { setOrder(event.target.value); setLimit(PAGE_SIZE); }}>
              <option value="title">{copy.catalogSortTitle}</option>
              <option value="newest">{copy.catalogSortNewest}</option>
              <option value="oldest">{copy.catalogSortOldest}</option>
            </select>
          </label>
        </div>
        <div className="search-hints">
          <p className="search-helper">{copy.catalogPublished} <strong>KAVI / Kuvi · Finna</strong> <span aria-hidden="true">·</span> <strong>{copy.catalogPartial}</strong>, {copy.catalogMediaUnverified}.</p>
          <button type="button" className="text-button" onClick={reset}>{copy.catalogClearFilters}</button>
        </div>
      </div>
      <div className="results-head" role="status" aria-live="polite">
        <div>
          <p className="eyebrow">{copy.catalogDocuments}</p>
          <h2>{format(matches.length)} {matches.length === 1 ? copy.catalogFoundOne : copy.catalogFoundMany}</h2>
        </div>
        <span className="results-chip">{copy.catalogMetadataNotice}</span>
      </div>
      {visible.length === 0 ? (
        <div className="empty-state">
          <strong>{copy.catalogEmpty}</strong>
          <p>{copy.catalogTryAgain}</p>
          <button type="button" className="text-button" onClick={reset}>{copy.catalogClearSearch}</button>
        </div>
      ) : (
        <div className="record-grid">
          {visible.map((item) => (
            <article className="record-card" key={item.id}>
              <div className="record-meta"><span>KAVI / FINNA</span><span>{item.year ?? copy.catalogYearUnavailable}</span></div>
              <div className="record-icon" aria-hidden="true">▣</div>
              <h3><Link href={"/acervo/kavi/" + encodeURIComponent(item.id) + "/"}>{item.title}</Link></h3>
              <p className="record-subject">{item.genres || item.subjects || copy.catalogSubjectsUnavailable}</p>
              <p className="record-id">{item.id}</p>
              <div className="record-footer">
                <span className="record-status">{copy.catalogRecordType}</span>
                <Link href={"/acervo/kavi/" + encodeURIComponent(item.id) + "/"} aria-label={copy.catalogViewLabel+" "+item.title}>{copy.catalogViewRecord}</Link>
              </div>
            </article>
          ))}
        </div>
      )}
      {matches.length > visible.length && (
        <div className="load-more">
          <button type="button" onClick={() => setLimit((value) => value + PAGE_SIZE)}>
            {copy.catalogMoreRecords} <span>({format(matches.length - visible.length)} {copy.catalogRemaining})</span>
          </button>
        </div>
      )}
    </section>
  );
}
