import kavi from "@/data/kavi-public.json";

export type RecordItem = {
  id: string;
  title: string;
  year: string | null;
  genres: string;
  subjects: string;
  languages: string;
  sourceUrl: string;
  source: string;
  institution: string;
  country: string;
  status: string;
  mediaAccess: string;
};

export const publicIndex = {
  total: kavi.total,
  observedOn: kavi.observedOn,
  catalogSha256: kavi.sourceCatalogSha256,
  scope: kavi.scope,
  metadataOnly: kavi.approvedMetadataPublication === true && kavi.mediaPlaybackVerified === false,
};

export const records: RecordItem[] = kavi.records;

export type Institution = {
  code: string;
  name: string;
  country: string;
  source: string;
  stage: "metadata" | "technical";
  count: number;
};

export const institutions: Institution[] = [
  {
    code: "kavi",
    name: "KAVI / Kuvi",
    country: "Finlândia",
    source: "Finna / Elonet",
    stage: "metadata",
    count: kavi.total,
  },
  {
    code: "eye",
    name: "Eye Filmmuseum",
    country: "Países Baixos",
    source: "Conector registrado · publicação não autorizada",
    stage: "technical",
    count: 0,
  },
  {
    code: "czech",
    name: "Czech Television",
    country: "Tchéquia",
    source: "Conector registrado · publicação não autorizada",
    stage: "technical",
    count: 0,
  },
  {
    code: "ciclic",
    name: "CICLIC",
    country: "França",
    source: "Conector registrado · publicação não autorizada",
    stage: "technical",
    count: 0,
  },
  {
    code: "asim",
    name: "Arxiu del So i de la Imatge",
    country: "Espanha",
    source: "Conector registrado · publicação não autorizada",
    stage: "technical",
    count: 0,
  },
  {
    code: "bnfa",
    name: "Bulgarian National Film Archive",
    country: "Bulgária",
    source: "Conector registrado · publicação não autorizada",
    stage: "technical",
    count: 0,
  },
];
