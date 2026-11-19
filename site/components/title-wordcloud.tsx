"use client";
import {useSiteLocale} from "@/components/site-locale";
import {institutionalDictionary} from "@/lib/institutional-dictionary";
import titleTerms from "@/data/title-wordcloud.json";

const terms = titleTerms.words.slice(0, 32);
const maxScore = Math.max(...terms.map((term) => term.score));
const minScore = Math.min(...terms.map((term) => term.score));

function wordStyle(score: number, index: number) {
  const normalized = (score - minScore) / Math.max(maxScore - minScore, 0.01);
  const size = 15 + Math.pow(normalized, 0.9) * 19;
  const rotation = [0, -3, 2, 0, 4, -2, 0][index % 7];
  return {
    fontSize: `${size.toFixed(1)}px`,
    transform: `rotate(${rotation}deg)`,
    opacity: Math.min(0.78 + normalized * 0.22, 1),
  };
}

/** Aggregated scientific visualization, never individual historical titles. */
export function TitleWordCloud() {
  const {locale}=useSiteLocale();
  const copy=institutionalDictionary[locale];
  const formatter=new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="en"?"en-US":"es-ES");
  return (
    <figure className="title-cloud" aria-label={copy.cloudAria}>
      <figcaption className="title-cloud-heading">{copy.cloudTitle}</figcaption>
      <div className="title-cloud-words" role="list" aria-label={copy.cloudList}>
        {terms.map((term, index) => (
          <span
            key={term.text}
            role="listitem"
            className={`title-cloud-term title-cloud-tone-${index % 5}`}
            style={wordStyle(term.score, index)}
            title={`${term.text}: ${formatter.format(term.count)} ${copy.cloudTitled} ${formatter.format(term.corpora)} ${copy.cloudCorpora}`}
            aria-label={`${term.text}, ${formatter.format(term.count)} ${copy.cloudTitled} ${formatter.format(term.corpora)} ${copy.cloudCorpora}`}
          >
            {term.text}
          </span>
        ))}
      </div>
      <figcaption className="title-cloud-footnote">
        {formatter.format(titleTerms.titlesExamined)} {copy.cloudExamined} · {titleTerms.corporaProcessed} {copy.cloudSources}.
        <span> {copy.cloudNotice}</span>
      </figcaption>
    </figure>
  );
}
