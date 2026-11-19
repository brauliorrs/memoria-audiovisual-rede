import {publicPageMetadata} from "@/lib/seo";
import type {Metadata} from "next";
import {TerritorialMap} from "@/components/territorial-map";
export const metadata=publicPageMetadata("/territorios/","Mapa científico de territórios","Distribuições agregadas por tema e país com geometria Natural Earth e evidências por corpus.");
export default function TerritoriesPage(){
  return <main className="shell page-shell"><TerritorialMap/></main>;
}
