import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {institutionalDictionary} from "@/lib/institutional-dictionary";
import {homeLanguages,publicPageMetadata} from "@/lib/seo";
type Props={params:Promise<{lang:string}>};
export const dynamicParams=false;
export function generateStaticParams(){return [{lang:"en"},{lang:"es"}];}
export async function generateMetadata({params}:Props):Promise<Metadata>{
 const {lang}=await params;
 if(lang!=="en"&&lang!=="es")return {robots:{index:false}};
 const c=institutionalDictionary[lang];
 return {...publicPageMetadata("/"+lang+"/",c.seoTitle,c.seoDescription),
  alternates:{canonical:"/"+lang+"/",languages:homeLanguages},
  openGraph:{type:"website",url:"/"+lang+"/",title:c.seoTitle,description:c.seoDescription,
   siteName:"MAR — Memória Audiovisual em Rede",locale:lang==="en"?"en_US":"es_ES"}};
}
export default async function LanguageLanding({params}:Props){
 const {lang}=await params;
 if(lang!=="en"&&lang!=="es")notFound();
 const c=institutionalDictionary[lang];
 return <div className="shell page-shell" lang={lang}>
  <p className="eyebrow">{c.homeEyebrow}</p>
  <h1>{c.landingTitle}</h1>
  <p className="page-lede">{c.landingIntro}</p>
  <div className="method-rows">
   <article><span>01</span><div><h2>{c.institutionTitle}</h2><p>{c.institutionIntro}</p><Link href="/instituicoes/">{c.institutionResearch} ↗</Link></div></article>
   <article><span>02</span><div><h2>{c.landingMethod}</h2><p>{c.kaviWarning}</p><Link href="/metodologia/">{c.landingMethod} ↗</Link></div></article>
   <article><span>03</span><div><h2>{c.landingCatalog}</h2><p>{c.kaviIntroEnd}</p><Link href="/acervo/">{c.landingCatalog} ↗</Link></div></article>
  </div>
  <p className="disclaimer">{c.landingNotice}</p>
 </div>;
}
