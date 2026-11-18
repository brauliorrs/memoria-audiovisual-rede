import type {Metadata} from "next";
import {CorpusComparison} from "@/components/corpus-comparison";

export const metadata:Metadata={
  title:"Comparação científica multícorpus",
  description:"Compare temas, países, plataformas e séries históricas entre duas ou três fontes do Memória Audiovisual em Rede, com proveniência e CSV de indicadores agregados."
};

export default function CompareCorporaPage(){
  return <main className="shell page-shell"><CorpusComparison/></main>;
}
