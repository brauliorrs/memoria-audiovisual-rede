import reports0 from "@/data/analytics-0.json";
import reports1 from "@/data/analytics-1.json";
import reports2 from "@/data/analytics-2.json";
import reports3 from "@/data/analytics-3.json";
import reports4 from "@/data/analytics-4.json";
import reports5 from "@/data/analytics-5.json";

export type HistoricalAnalyticReport = {
  code: string;
  source: string;
  totalInstitutions: number;
  institutionsWithVideo: number;
  withEmbeds: number;
  siteStatus: Record<string,number>;
  integrity: Record<string,number>;
  platforms: Record<string,number>;
  continents: Record<string,number>;
  videoContinents: Record<string,number>;
};

export const historicalAnalyticReports: HistoricalAnalyticReport[] = [
  ...reports0,...reports1,...reports2,...reports3,...reports4,...reports5
] as unknown as HistoricalAnalyticReport[];

const CORPUS_TO_REPORT: Record<string,string> = {
  "czech-television":"czech_tv",
  "estonian_film_archive":"efa_estonia",
  "cinemateca-portuguesa":"cinemateca_pt",
  "european-film-gateway":"efg",
  "filmmuseum_dusseldorf":"filmmuseum_dusseldorf",
  "filmoteca-vasca":"filmoteca_vasca",
  "filmoteca-espanola":"filmoteca_espanola",
  "filmoteca-catalunya":"filmoteca_catalunya",
  "filmoteca_valenciana":"filmoteca_valenciana",
  "home-movies-memoryscapes":"home_movies",
  "ifi_archive_player":"ifi_archive_player",
  "murnau_stiftung":"murnau_stiftung",
  "saint-etienne":"saint_etienne",
  "csc-cineteca-nazionale":"csc_cineteca",
  "aqshf":"aqshf",
  "portal-portugues-arquivos":"ppa",
  "image_est":"image_est",
  "cna":"cna",
  "sfa":"sfa",
};

export function getAnalyticReport(corpusCode: string) {
  const key = CORPUS_TO_REPORT[corpusCode] ?? corpusCode.replaceAll("-","_");
  return historicalAnalyticReports.find(item=>item.code===key);
}

export function rankSummary(values: Record<string,number>, limit = 12) {
  return Object.entries(values).filter(([,value])=>Number.isFinite(value)&&value>0).sort((a,b)=>b[1]-a[1]).slice(0,limit);
}
