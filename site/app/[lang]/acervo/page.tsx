import {notFound} from "next/navigation";
import type {Metadata} from "next";
import {localizedPageSeo} from "@/lib/seo";
import OriginalPage from "@/app/(pt)/acervo/page";

type Props={params:Promise<{lang:string}>};
export async function generateMetadata({params}:Props):Promise<Metadata>{
 const {lang}=await params;
 if(lang!=="en"&&lang!=="es")notFound();
 return localizedPageSeo("/acervo/",lang);
}
export default function Page(){return <OriginalPage/>;}
