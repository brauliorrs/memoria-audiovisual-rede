"use client";
import {useSiteLocale} from "@/components/site-locale";
import {institutionalDictionary,type InstitutionalKey} from "@/lib/institutional-dictionary";
export function InstitutionalText({id}:{id:InstitutionalKey}){
  const {locale}=useSiteLocale();
  return <>{institutionalDictionary[locale][id]}</>;
}
