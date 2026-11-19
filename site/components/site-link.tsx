"use client";
import NextLink from "next/link";
import type {ComponentProps} from "react";
import {useSiteLocale} from "@/components/site-locale";
import {localizedHref} from "@/lib/locale-routes";

export default function SiteLink(props:ComponentProps<typeof NextLink>){
 const {locale}=useSiteLocale();
 const href=typeof props.href==="string"?localizedHref(props.href,locale):props.href;
 return <NextLink {...props} href={href}/>;
}
