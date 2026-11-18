import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { historicalAnalyticReports } from "@/lib/historical-analytics";

export type AnalyticRow = Record<string,string>;
export type ResearchDimension = "resumo_temas"|"tema_pais"|"tema_plataforma"|"tema_tipo_arquivo"|"linha_do_tempo_corpus"|"resumo_instituicoes";
const supported:ResearchDimension[]=["resumo_temas","tema_pais","tema_plataforma","tema_tipo_arquivo","linha_do_tempo_corpus","resumo_instituicoes"];
export const dimensions=supported;
const ROOT=resolve(process.cwd(),"..","data","output");

export function parseCsv(raw:string):AnalyticRow[] {
 const rows:string[][]=[];let row:string[]=[],value="",quoted=false;
 for(let i=0;i<raw.length;i++){const c=raw[i];if(quoted){if(c==='"'&&raw[i+1]==='"'){value+='"';i++;}else if(c==='"')quoted=false;else value+=c;}else if(c==='"')quoted=true;else if(c===','){row.push(value);value="";}else if(c==='\n'){row.push(value.replace(/\r$/,""));rows.push(row);row=[];value="";}else value+=c;}
 if(row.length||value){row.push(value);rows.push(row)}
 const headings=(rows.shift()??[]).map(x=>x.replace(/^\uFEFF/,""));
 return rows.filter(r=>r.length===headings.length).map(r=>Object.fromEntries(headings.map((h,i)=>[h,r[i]])));
}

export function loadResearchData(code:string,dimension:ResearchDimension):AnalyticRow[]{
 if(!historicalAnalyticReports.some(r=>r.code===code)||!supported.includes(dimension))return [];
 const path=resolve(ROOT,`${code}_${dimension}.csv`);
 if(!path.startsWith(ROOT+"/")||!existsSync(path))return [];
 return parseCsv(readFileSync(path,"utf8"));
}
export function researchSourceCodes(){return historicalAnalyticReports.map(r=>r.code)}
