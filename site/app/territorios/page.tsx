import type {Metadata} from "next";
import {TerritorialMap} from "@/components/territorial-map";
export const metadata:Metadata={
  title:"Mapa territorial dos acervos — MAR",
  description:"Mapa mundial de indicadores agregados tema×país, com geometria Natural Earth e rastreabilidade científica por corpus."
};
export default function TerritoriesPage(){
  return <main className="shell page-shell"><TerritorialMap/></main>;
}
