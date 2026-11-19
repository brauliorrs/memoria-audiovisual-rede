import type {ReactNode} from "react";
import {siteMetadata,SiteShell} from "@/components/site-shell";
import "../globals.css";

export const metadata=siteMetadata;
export default function PortugueseRootLayout({children}:{children:ReactNode}){
 return <html lang="pt-BR"><body><SiteShell locale="pt">{children}</SiteShell></body></html>;
}
