import titleTerms from "@/data/title-wordcloud.json";

const formatter = new Intl.NumberFormat("pt-BR");
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
  return (
    <figure className="title-cloud" aria-label="Nuvem de palavras frequentes nos títulos audiovisuais">
      <figcaption className="title-cloud-heading">O QUE APARECE NOS TÍTULOS</figcaption>
      <div className="title-cloud-words" role="list" aria-label="Termos recorrentes em múltiplas fontes">
        {terms.map((term, index) => (
          <span
            key={term.text}
            role="listitem"
            className={`title-cloud-term title-cloud-tone-${index % 5}`}
            style={wordStyle(term.score, index)}
            title={`${term.text}: ${formatter.format(term.count)} títulos em ${formatter.format(term.corpora)} corpora`}
            aria-label={`${term.text}, presente em ${formatter.format(term.count)} títulos de ${term.corpora} corpora`}
          >
            {term.text}
          </span>
        ))}
      </div>
      <figcaption className="title-cloud-footnote">
        {formatter.format(titleTerms.titlesExamined)} registros analisados · {titleTerms.corporaProcessed} fontes.
        <span> Frequências agregadas; sem exposição de títulos ou filmes.</span>
      </figcaption>
    </figure>
  );
}
