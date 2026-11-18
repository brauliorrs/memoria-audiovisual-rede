import institutions0 from "@/data/institution-profiles-0.json";
import institutions1 from "@/data/institution-profiles-1.json";
import institutions2 from "@/data/institution-profiles-2.json";
import institutions3 from "@/data/institution-profiles-3.json";
import institutions4 from "@/data/institution-profiles-4.json";
import institutions5 from "@/data/institution-profiles-5.json";
import institutions6 from "@/data/institution-profiles-6.json";
import {getAnalyticReport} from "@/lib/historical-analytics";
export interface InstitutionProfile {
 id:string;name:string;country:string;continent:string;type:string;repositoryCode:string;originUrl:string;
}
export interface InstitutionGroup {
 source:string;sampled:boolean;rows:InstitutionProfile[];licencePolicy?:string;attribution?:string;
}
const allGroups=Object.assign({},institutions0,institutions1,institutions2,institutions3,institutions4,institutions5,institutions6) as unknown as Record<string,InstitutionGroup>;
export const institutionGroups:Record<string,InstitutionGroup>=allGroups;
export const institutionSources=Object.keys(allGroups).sort();
export const institutionalProfiles=Object.entries(allGroups).flatMap(([source,group])=>group.rows.map(item=>({...item,source})));
export function getInstitutionGroup(corpusCode:string):InstitutionGroup|undefined {
 const key=getAnalyticReport(corpusCode)?.code??corpusCode.replaceAll("-","_");
 return allGroups[key];
}
export function findInstitution(source:string,index:string){
 const group=allGroups[source];
 if(!group||!/^[1-9][0-9]*$/.test(index))return undefined;
 return group.rows.find(x=>x.id===`${source}:${index}`);
}
