import {recordSeo} from "@/lib/seo";
import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {institutionalProfiles,findInstitution,institutionGroups} from "@/lib/institutional-profiles";
import {LocalizedText} from "@/components/site-locale";
import {ScientificText} from "@/components/scientific-i18n";
export const dynamicParams=false;
export function generateStaticParams(){return institutionalProfiles.map(i=>({source:i.source,entry:i.id.split(":")[1]}));}
export async function generateMetadata({params}:{params:Promise<{source:string;entry:string}>}):Promise<Metadata>{const {source,entry}=await params;const p=findInstitution(source,entry);
 return p?recordSeo("/instituicoes/pesquisa/"+encodeURIComponent(source)+"/"+encodeURIComponent(entry)+"/",
  `${p.name} — Perfil institucional`,
  "Perfil institucional de pesquisa histórica no MAR: fontes e links de origem; acesso atual e direitos de mídia não verificados.") :
  {title:"Instituição não identificada",robots:{index:false}};}
export default async function InstitutionalProfilePage({params}:{params:Promise<{source:string;entry:string}>}){
 const {source,entry}=await params;
 const profile=findInstitution(source,entry);
 if(!profile)notFound();
 const group=institutionGroups[source];
 return <main className="shell page-shell">
  <nav className="ob-breadcrumb" aria-label="Breadcrumb"><Link href="/instituicoes/pesquisa/"><LocalizedText id="navInstitutions"/></Link><span>/</span><span>{source.toUpperCase()}</span></nav>
  <p className="eyebrow"><ScientificText id="instEyebrow"/></p>
  <h1>{profile.name}</h1>
  <p className="page-lede"><LocalizedText id="institutionIntro"/></p>
  <div className="ob-profile-tags"><span>{source.toUpperCase()}</span><span>{profile.country||"—"}</span>{profile.continent&&<span>{profile.continent}</span>}</div>
  <section className="ob-profile-columns">
   <article className="ob-panel"><h2><LocalizedText id="navInstitutions"/></h2>
    <dl className="research-institution-fields">
     <div><dt><LocalizedText id="source"/></dt><dd>{source.toUpperCase()}</dd></div>
     <div><dt><LocalizedText id="country"/></dt><dd>{profile.country||"—"}</dd></div>
     <div><dt><ScientificText id="instType"/></dt><dd>{profile.type||"—"}</dd></div>
     <div><dt><ScientificText id="instSourceId"/></dt><dd>{profile.repositoryCode||"—"}</dd></div>
    </dl>
   </article>
   <article className="ob-panel"><h2><LocalizedText id="origin"/></h2>
    {profile.originUrl?<p><a href={profile.originUrl} target="_blank" rel="noopener noreferrer"><LocalizedText id="origin"/> ↗</a></p>:<p>—</p>}
    <p><LocalizedText id="snapshotOnly"/></p>
    <p><strong><ScientificText id="instDataSource"/>:</strong> {group.source}</p>
    {group.licencePolicy&&<p><a href={group.licencePolicy} rel="noopener noreferrer" target="_blank"><ScientificText id="instPolicy"/></a></p>}
    {group.attribution&&<p>{group.attribution}</p>}
   </article>
  </section>
  <p className="disclaimer"><LocalizedText id="historicalWarning"/> <LocalizedText id="sourceNote"/></p>
  <p><Link href="/instituicoes/pesquisa/"><LocalizedText id="back"/></Link></p>
 </main>;
}
