"use client";

import Link from "next/link";
import type {RecordItem} from "@/lib/catalog";
import {useScientificCopy} from "@/components/scientific-i18n";
import {useSiteLocale} from "@/components/site-locale";

type RecordDetailProps={
  record:RecordItem;
  catalogCount:number;
  observedOn:string;
  approvedCatalogSha256:string;
};

/**
 * Only editorial labels are translated. Original KAVI/Finna metadata is
 * displayed literally, without machine translation or metadata mutation.
 * This UI has no media player and never fetches another corpus.
 */
export function KaviRecordDetail({record,catalogCount,observedOn,approvedCatalogSha256}:RecordDetailProps){
  const copy=useScientificCopy();
  const {locale}=useSiteLocale();
  const formattedCount=new Intl.NumberFormat(
    locale==="pt"?"pt-BR":locale==="es"?"es-ES":"en-US"
  ).format(catalogCount);

  const fields=[
    {label:copy.kaviFieldId,value:record.id},
    {label:copy.kaviFieldYear,value:record.year??copy.kaviUnknown},
    {label:copy.kaviFieldGenres,value:record.genres||copy.kaviGenresUnknown},
    {label:copy.kaviFieldSubjects,value:record.subjects||copy.kaviSubjectsUnknown},
    {label:copy.kaviFieldLanguage,value:record.languages||copy.kaviUnknown},
    {label:copy.kaviFieldInstitution,value:record.institution},
    {label:copy.kaviFieldCountry,value:record.country},
    {label:copy.kaviFieldService,value:record.source},
  ];

  return (
    <div className="shell page-shell record-detail">
      <nav aria-label={copy.kaviBreadcrumb} className="record-breadcrumb">
        <Link href="/acervo/">{copy.kaviArchive}</Link><span aria-hidden="true">/</span>
        <Link href="/instituicoes/kavi/">KAVI / Kuvi</Link><span aria-hidden="true">/</span>
        <span aria-current="page">{copy.kaviRecord}</span>
      </nav>
      <p className="eyebrow">{copy.kaviEyebrow}</p>
      <h1>{record.title}</h1>
      <p className="page-lede">{copy.kaviIntro}</p>
      <div className="record-detail-grid">
        <section aria-labelledby="ficha-dados" className="detail-panel">
          <h2 id="ficha-dados">{copy.kaviDetailsHeading}</h2>
          <dl className="metadata-list">
            {fields.map(({label,value})=>(
              <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
            ))}
          </dl>
          <a className="button button-dark detail-source-link" href={record.sourceUrl}
            target="_blank" rel="noopener noreferrer">{copy.kaviOpenSource}</a>
          <p className="detail-external-note">{copy.kaviExternalNote}</p>
          <p className="disclaimer">{copy.kaviOriginalMetadataNote}</p>
        </section>
        <aside className="detail-panel detail-provenance" aria-labelledby="ficha-proveniencia">
          <h2 id="ficha-proveniencia">{copy.kaviProvenanceHeading}</h2>
          <p className="document-pill">{copy.kaviProvenancePill}</p>
          <dl className="metadata-list">
            <div><dt>{copy.kaviScientificReview}</dt><dd>{copy.kaviReviewStatus}</dd></div>
            <div><dt>{copy.kaviPlaybackLabel}</dt><dd>{copy.kaviPlaybackStatus}</dd></div>
            <div><dt>{copy.kaviMediaRightsLabel}</dt><dd>{copy.kaviMediaRightsStatus}</dd></div>
            <div><dt>{copy.kaviReferenceIndex}</dt><dd>KAVI/Finna · {formattedCount} {copy.kaviCountUnit}</dd></div>
            <div><dt>{copy.kaviObservationDate}</dt><dd>{observedOn}</dd></div>
          </dl>
          <p className="provenance-hash"><strong>{copy.kaviApprovedHash}</strong><code>{approvedCatalogSha256}</code></p>
        </aside>
      </div>
      <p className="detail-bottom-link">
        <Link href="/instituicoes/kavi/">← {copy.kaviBackToCatalog}</Link>
      </p>
    </div>
  );
}
