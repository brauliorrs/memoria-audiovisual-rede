import type { Metadata } from "next";
import { CatalogSearch } from "@/components/catalog-search";
import { publicIndex, records } from "@/lib/catalog";

export const metadata: Metadata = { title: "Catálogo público" };
export default function AcervoPage() {
  return <div className="shell page-shell">
    <p className="eyebrow">PESQUISA NO MAR</p>
    <h1>Catálogo audiovisual</h1>
    <p className="page-lede">Acesse as fichas documentais publicadas. Nesta primeira versão do site, a coleção pesquisável contém {publicIndex.total} registros KAVI/Finna, com cobertura parcial e reprodução não verificada.</p>
    <CatalogSearch items={records} />
  </div>;
}
