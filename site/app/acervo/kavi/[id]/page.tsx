import type {Metadata} from "next";
import {notFound} from "next/navigation";
import {publicIndex,records} from "@/lib/catalog";
import {KaviRecordDetail} from "@/components/kavi-record-detail";

type Props={params:Promise<{id:string}>};

export function generateStaticParams(){
  return records.map((record) => ({ id: record.id }));
}

export async function generateMetadata({params}:Props):Promise<Metadata>{
  const {id}=await params;
  const record=records.find((item)=>item.id===id);
  if(!record)return {title:"Ficha não encontrada"};
  return {
    title:record.title+" — KAVI / Finna",
    description:"Ficha documental publicada no MAR: "+record.title+". Metadados de origem, proveniência e situação de validação.",
  };
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
