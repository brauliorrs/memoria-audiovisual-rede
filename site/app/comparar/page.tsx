import {pageSeo} from "@/lib/seo";
import type {Metadata} from "next";
import {CorpusComparison} from "@/components/corpus-comparison";

export const metadata=pageSeo("/comparar/");

export default function CompareCorporaPage(){
  return <main className="shell page-shell"><CorpusComparison/></main>;
}
