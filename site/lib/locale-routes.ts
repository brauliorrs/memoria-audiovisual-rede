import type {SiteLocale} from "@/components/site-locale";
import {STATIC_ROUTES,type StaticRoute} from "@/lib/seo";

/** Only emit locale URLs for the 14 actually exported static pages. */
export function localizedHref(href:string,locale:SiteLocale):string{
 if(!href.startsWith("/")||href.startsWith("//"))return href;
 const match=/^([^?#]*)(.*)$/.exec(href);
 if(!match)return href;
 const original=match[1];
 const suffix=match[2];
 const unprefixed=original.replace(/^\/(?:en|es)(?=\/|$)/,"")||"/";
 const canonical=unprefixed.endsWith("/")?unprefixed:unprefixed+"/";
 if(!STATIC_ROUTES.includes(canonical as StaticRoute))return href;
 return (locale==="pt"?canonical:"/"+locale+canonical)+suffix;
}
