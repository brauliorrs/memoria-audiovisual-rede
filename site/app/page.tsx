import type {Metadata} from "next";
import Link from "next/link";
import {CatalogSearch} from "@/components/catalog-search";
import {TitleWordCloud} from "@/components/title-wordcloud";
import {InstitutionalText} from "@/components/institutional-i18n";
import {publicIndex,records} from "@/lib/catalog";

export const metadata:Metadata={title:"Memória Audiovisual em Rede — observatório científico"};

export default function HomePage(){
 return <>
  <section className="hero">
   <div className="shell hero-inner">
    <div className="hero-copy">
     <p className="eyebrow eyebrow-light"><span className="live-dot"/><InstitutionalText id="homeEyebrow"/></p>
     <h1><InstitutionalText id="homeTitleLead"/> <em><InstitutionalText id="homeTitleEm"/></em></h1>
     <p className="hero-description"><InstitutionalText id="homeIntro"/></p>
     <div className="hero-actions">
      <Link className="button button-light" href="/observatorio/"><InstitutionalText id="homeExplore"/> <span aria-hidden="true">↗</span></Link>
      <Link className="button button-outline" href="/comparar/"><InstitutionalText id="homeCompare"/> <span aria-hidden="true">→</span></Link>
     </div>
    </div>
    <div className="hero-visual hero-wordcloud"><TitleWordCloud/></div>
   </div>
  </section>
  <section className="numbers"><div className="shell numbers-grid">
   <div><span className="number">{publicIndex.total}</span><span className="number-label"><InstitutionalText id="homeKaviCount"/></span></div>
   <div><span className="number">1</span><span className="number-label"><InstitutionalText id="homeSourceCount"/></span></div>
   <div><span className="number">100%</span><span className="number-label"><InstitutionalText id="homeSourceLinks"/></span></div>
   <div><span className="number">0</span><span className="number-label"><InstitutionalText id="homeHostedMedia"/></span></div>
  </div></section>
  <section className="shell intro-section">
   <div className="section-intro">
    <div><p className="eyebrow"><InstitutionalText id="homeResearchLabel"/></p><h2><InstitutionalText id="homeResearchTitle"/></h2></div>
    <p><InstitutionalText id="homeResearchNote"/></p>
   </div>
   <CatalogSearch items={records}/>
  </section>
  <section className="principles-band"><div className="shell principles-inner">
   <div><p className="eyebrow eyebrow-light"><InstitutionalText id="homeCommitLabel"/></p><h2><InstitutionalText id="homeCommitTitle"/></h2></div>
   <div className="principles-list">
    <p><span>01</span> <InstitutionalText id="homePrinciple1"/></p>
    <p><span>02</span> <InstitutionalText id="homePrinciple2"/></p>
    <p><span>03</span> <InstitutionalText id="homePrinciple3"/></p>
   </div>
  </div></section>
 </>;
}
