import part0 from "@/data/research-slices-0.json";
import part1 from "@/data/research-slices-1.json";
import part2 from "@/data/research-slices-2.json";
import part3 from "@/data/research-slices-3.json";
import part4 from "@/data/research-slices-4.json";
import part5 from "@/data/research-slices-5.json";
import part6 from "@/data/research-slices-6.json";
import part7 from "@/data/research-slices-7.json";
import part8 from "@/data/research-slices-8.json";
import part9 from "@/data/research-slices-9.json";
import part10 from "@/data/research-slices-10.json";
import part11 from "@/data/research-slices-11.json";
import part12 from "@/data/research-slices-12.json";
import part13 from "@/data/research-slices-13.json";
import part14 from "@/data/research-slices-14.json";
import part15 from "@/data/research-slices-15.json";
import { getAnalyticReport } from "@/lib/historical-analytics";

export interface TopicCountry {tema:string; pais:string; total:string}
export interface TopicPlatform {tema:string; plataforma:string; total:string}
export interface Observation {
 dataset:string;
 observation_key:string;
 snapshot_generated_at:string;
 source_status_date:string;
 institutions:string;
 institutions_with_video_links:string;
 video_links_total:string;
 videos_in_curatorial_catalog:string;
 countries_with_videos:string;
 platforms_detected:string;
}
type ReportSlice<T>={source:string;rows:T[];error?:string};
export interface ResearchSlice {
 tema_pais:ReportSlice<TopicCountry>;
 tema_plataforma:ReportSlice<TopicPlatform>;
 linha_do_tempo_corpus:ReportSlice<Observation>;
}
const merged:Record<string,ResearchSlice>=Object.assign({},part0,part1,part2,part3,part4,part5,part6,part7,part8,part9,part10,part11,part12,part13,part14,part15) as unknown as Record<string,ResearchSlice>;
export const researchSlices:Record<string,ResearchSlice>=merged;
export const researchSourceCodes=Object.keys(merged).sort((a,b)=>a.localeCompare(b,"pt-BR"));
export function getResearchSlice(corpusCode:string):ResearchSlice|undefined {
 const key=getAnalyticReport(corpusCode)?.code??corpusCode.replaceAll("-","_");
 return merged[key];
}
export function verifiedCount(raw:string|undefined) {
 const n=Number(raw);
 return Number.isSafeInteger(n)&&n>=0?n:0;
}
export function summarizeTopics(slice:ResearchSlice) {
 const counts=new Map<string,number>();
 for(const row of slice.tema_plataforma.rows)counts.set(row.tema,(counts.get(row.tema)||0)+verifiedCount(row.total));
 if(!counts.size)for(const row of slice.tema_pais.rows)counts.set(row.tema,(counts.get(row.tema)||0)+verifiedCount(row.total));
 return Array.from(counts,([name,total])=>({name,total})).sort((a,b)=>b.total-a.total||a.name.localeCompare(b.name));
}
export function chronologicalObservations(slice:ResearchSlice){
 return [...slice.linha_do_tempo_corpus.rows].filter(r=>!Number.isNaN(Date.parse(r.snapshot_generated_at))&&r.snapshot_generated_at)
   .sort((a,b)=>Date.parse(a.snapshot_generated_at)-Date.parse(b.snapshot_generated_at));
}
export const temporalMetrics={
 video_links_total:"videoLinks",institutions:"institutions",institutions_with_video_links:"institutionsWithVideo",
 videos_in_curatorial_catalog:"thematicCatalog",countries_with_videos:"countries"
} as const;
