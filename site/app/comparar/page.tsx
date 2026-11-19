import {publicPageMetadata} from "@/lib/seo";
import type {Metadata} from "next";
import {CorpusComparison} from "@/components/corpus-comparison";

export const metadata=publicPageMetadata("/comparar/","Comparação científica de corpora","Comparação de até três acervos por temas, países, plataformas e datas de coleta, com rastreabilidade e exportações agregadas.");

export default function CompareCorporaPage(){
  return <main className="shell page-shell"><CorpusComparison/></main>;
}
