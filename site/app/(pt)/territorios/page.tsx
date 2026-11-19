import {pageSeo} from "@/lib/seo";
import type {Metadata} from "next";
import {TerritorialMap} from "@/components/territorial-map";
export const metadata=pageSeo("/territorios/");
export default function TerritoriesPage(){
  return <main className="shell page-shell"><TerritorialMap/></main>;
}
