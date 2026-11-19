import type {ReactNode} from "react";
import {notFound} from "next/navigation";
import {siteMetadata,SiteShell} from "@/components/site-shell";
import "../globals.css";

export const metadata=siteMetadata;
export const dynamicParams=false;
export function generateStaticParams(){return [{lang:"en"},{lang:"es"}];}
export default async function LocalizedRootLayout({children,params}:{children:ReactNode;params:Promise<{lang:string}>}){
 const {lang}=await params;
 if(lang!=="en"&&lang!=="es")notFound();
 return <html lang={lang}><body><SiteShell locale={lang}>{children}</SiteShell></body></html>;
}
