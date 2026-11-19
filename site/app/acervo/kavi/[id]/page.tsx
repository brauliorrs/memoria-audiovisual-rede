import type {Metadata} from "next";
import {notFound} from "next/navigation";
import {publicIndex,records} from "@/lib/catalog";
import {KaviRecordDetail} from "@/components/kavi-record-detail";
import {publicPageMetadata} from "@/lib/seo";

type Props={params:Promise<{id:string}>};

export function generateStaticParams(){
  return records.map((record) => ({ id: record.id }));
}

export async function generateMetadata({params}:Props):Promise<Metadata>{
  const {id}=await params;
  const record=records.find((item)=>item.id===id);
  if(!record)return {title:"Ficha não encontrada"};
  return publicPageMetadata("/acervo/kavi/"+encodeURIComponent(record.id)+"/",record.title+" — KAVI / Finna","Ficha documental KAVI/Finna: "+record.title+". Metadados de origem com proveniência; reprodução, direitos de mídia e revisão científica individual não verificados.");
}

export default async function KaviRecordPage({params}:Props){
  const {id}=await params;
  const record=records.find((item)=>item.id===id);
  if(!record)notFound();
  return <KaviRecordDetail
    record={record}
    catalogCount={publicIndex.total}
    observedOn={publicIndex.observedOn}
    approvedCatalogSha256={publicIndex.catalogSha256}
  />;
}
