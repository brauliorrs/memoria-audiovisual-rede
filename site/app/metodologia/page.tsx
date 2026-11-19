import {publicPageMetadata} from "@/lib/seo";
import type { Metadata } from "next";
import Link from "next/link";
import {ScientificText} from "@/components/scientific-i18n";

export const metadata=publicPageMetadata("/metodologia/","Metodologia científica","Proveniência, revisão independente, estados de admissão documental e limites jurídicos de pesquisa do MAR.");
export default function MethodologyPage() {
  return <div className="shell page-shell methodology">
    <p className="eyebrow"><ScientificText id="metEyebrow"/></p>
    <h1><ScientificText id="metTitle"/></h1>
    <p className="page-lede"><ScientificText id="metIntro"/></p>
    <div className="method-rows">
      <article><span>01</span><div><h2><ScientificText id="metHeading1"/></h2><p><ScientificText id="metDesc1"/></p></div></article>
      <article><span>02</span><div><h2><ScientificText id="metHeading2"/></h2><p><ScientificText id="metDesc2"/></p></div></article>
      <article><span>03</span><div><h2><ScientificText id="metHeading3"/></h2><p><ScientificText id="metDesc3"/></p></div></article>
      <article><span>04</span><div><h2><ScientificText id="metHeading4"/></h2><p><ScientificText id="metDesc4"/></p></div></article>
    </div>
    <div className="method-cta"><p><ScientificText id="metCta"/></p><Link className="button button-dark" href="/acervo/"><ScientificText id="metButton"/></Link></div>
  </div>;
}
