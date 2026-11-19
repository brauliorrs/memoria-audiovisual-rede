import type {Metadata} from "next";
import {LocalizedText} from "@/components/site-locale";
import {InstitutionalText} from "@/components/institutional-copy";
import {publicPageMetadata} from "@/lib/seo";
import {InstitutionBrowser} from "@/components/institution-browser";
export const metadata=publicPageMetadata("/instituicoes/pesquisa/","Instituições de pesquisa","Perfis institucionais históricos com referência à origem, limites de acesso e evidências documentais.");
export default function InstitutionsResearchPage(){return <main className="shell page-shell"><p className="eyebrow"><InstitutionalText id="institutionResearchEyebrow"/></p><h1><LocalizedText id="institutionTitle"/></h1><p className="page-lede"><LocalizedText id="institutionIntro"/></p><InstitutionBrowser/></main>;}
