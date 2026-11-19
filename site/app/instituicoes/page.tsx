import {pageSeo} from "@/lib/seo";
import type {Metadata} from "next";
import Link from "next/link";
import {institutions} from "@/lib/catalog";
import {InstitutionalText,InstitutionalCountry} from "@/components/institutional-i18n";

export const metadata=pageSeo("/instituicoes/");

export default function InstitutionsPage(){
 return <div className="shell page-shell">
  <p className="eyebrow"><InstitutionalText id="institutionsEyebrow"/></p>
  <h1><InstitutionalText id="institutionsTitle"/></h1>
  <p className="page-lede"><InstitutionalText id="institutionsIntro"/></p>
  <p><Link href="/instituicoes/pesquisa/"><InstitutionalText id="institutionsResearchLink"/> ↗</Link> · <Link href="/indice-acesso/"><InstitutionalText id="institutionsAccessLink"/> ↗</Link></p>
  <div className="institution-grid">
   {institutions.map(item=><article className="institution-card" key={item.code}>
    <div className="institution-top"><span><InstitutionalCountry name={item.country}/></span>
     <span className={item.stage==="metadata"?"state state-ready":"state state-waiting"}>
      <InstitutionalText id={item.stage==="metadata"?"institutionsPublished":"institutionsPending"}/>
     </span>
    </div>
    <h2>{item.name}</h2>
    <p>{item.stage==="metadata"?item.source:<InstitutionalText id="institutionsConnectorNotApproved"/>}</p>
    <div className="institution-bottom">
     <span>{item.stage==="metadata"?<>{item.count} <InstitutionalText id="institutionsCount"/></>:<InstitutionalText id="institutionsNone"/>}</span>
     {item.stage==="metadata"&&<Link href="/instituicoes/kavi/"><InstitutionalText id="institutionsConsult"/> ↗</Link>}
    </div>
   </article>)}
  </div>
  <p className="disclaimer"><InstitutionalText id="institutionsDisclaimer"/></p>
 </div>;
}
