import type {Metadata} from "next";
import {LocalizedText} from "@/components/site-locale";
import {InstitutionBrowser} from "@/components/institution-browser";
export const metadata:Metadata={title:"Instituições de pesquisa — MAR"};
export default function InstitutionsResearchPage(){return <main className="shell page-shell"><p className="eyebrow">MAR · INSTITUTIONAL RESEARCH</p><h1><LocalizedText id="institutionTitle"/></h1><p className="page-lede"><LocalizedText id="institutionIntro"/></p><InstitutionBrowser/></main>;}
