import {notFound} from "next/navigation";
import type {Metadata} from "next";
import {localizedPageSeo} from "@/lib/seo";
import OriginalPage from "@/app/(pt)/indice-acesso/page";

type Props={params:Promise<{lang:string}>};
export async function generateMetadata({params}:Props):Promise<Metadata>{
 const {lang}=await params;
 if(lang!=="en"&&lang!=="es")notFound();
 return localizedPageSeo("/indice-acesso/",lang);
}
export default function Page(){return <OriginalPage/>;}
