import type {Metadata} from "next";
export const PUBLIC_ORIGIN="https://mar-public-site.vercel.app";
/* The only static server-rendered, indexable language alternatives presently available. */
export const homeLanguages={"pt-BR":"/",en:"/en/",es:"/es/","x-default":"/"} as const;
export function publicPageMetadata(path:string,title:string,description:string):Metadata{
 return {title,description,alternates:{canonical:path},
  openGraph:{type:"website",url:path,title,description,siteName:"MAR — Memória Audiovisual em Rede"},
  robots:{index:true,follow:true}};
}
