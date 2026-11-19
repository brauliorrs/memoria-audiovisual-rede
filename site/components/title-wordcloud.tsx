"use client";

import titleTerms from "@/data/title-wordcloud.json";
import {useSiteLocale} from "@/components/site-locale";
import {institutionalCopy} from "@/components/institutional-i18n";

const terms=titleTerms.words.slice(0,32);
const maxScore=Math.max(...terms.map(t=>t.score));
const minScore=Math.min(...terms.map(t=>t.score));

function wordStyle(score:number,index:number){
 const normalized=(score-minScore)/Math.max(maxScore-minScore,0.01);
 const size=15+Math.pow(normalized,0.9)*19;
 const rotation=[0,-3,2,0,4,-2,0][index%7];
 return {fontSize:`${size.toFixed(1)}px`,transform:`rotate(${rotation}deg)`,opacity:Math.min(0.78+normalized*0.22,1)};
}

/** Only display precomputed aggregate terms; never publish individual source titles. */
export function TitleWordCloud(){
 const {locale}=useSiteLocale();
 const t=institutionalCopy[locale];
 const formatter=new Intl.NumberFormat(locale==="pt"?"pt-BR":locale==="en"?"en-US":"es-ES");
 return <figure className="title-cloud" aria-label={t.cloudAria}>
  <figcaption className="title-cloud-heading">{t.cloudHeading}</figcaption>
  <div className="title-cloud-words" role="list" aria-label={t.cloudListAria}>
   {terms.map((term,index)=><span
    key={term.text}
    role="listitem"
    className={`title-cloud-term title-cloud-tone-${index%5}`}
    style={wordStyle(term.score,index)}
    title={`${term.text}: ${formatter.format(term.count)} ${t.cloudCount} · ${formatter.format(term.corpora)} ${t.cloudCorpora}`}
    aria-label={`${term.text}, ${formatter.format(term.count)} ${t.cloudCount}, ${formatter.format(term.corpora)} ${t.cloudCorpora}`}
   >{term.text}</span>)}
  </div>
  <figcaption className="title-cloud-footnote">
   {formatter.format(titleTerms.titlesExamined)} {t.cloudRecords} · {formatter.format(titleTerms.corporaProcessed)} {t.cloudSources}.
   <span> {t.cloudFoot}</span>
  </figcaption>
 </figure>;
}
