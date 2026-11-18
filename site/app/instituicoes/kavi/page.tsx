import type { Metadata } from "next";
import Link from "next/link";
import { CatalogSearch } from "@/components/catalog-search";
import { publicIndex, records } from "@/lib/catalog";

export const metadata: Metadata = { title: "KAVI / Finna" };
export default function KaviPage() {
  return <div className="shell page-shell">
    <Link href="/instituicoes/" className="back-link">← Todas as instituições</Link>
    <p className="eyebrow">FINLÂNDIA · FINNA / ELONET</p>
    <h1>KAVI / Kuvi</h1>
    <p className="page-lede">Kansallinen audiovisuaalinen instituutti. O índice inicial contém {publicIndex.total} fichas descritivas com links para registros de origem. Cobertura parcial e revisão individual não concluída.</p>
    <div className="notice"><strong>Nota de integridade científica</strong><p>As fichas foram aprovadas para publicação como metadados. Isso não demonstra disponibilidade de reprodução, domínio público, custódia do filme ou conclusão da análise científica do corpus.</p><small>Referência da coleta: {publicIndex.observedOn} · SHA-256 do CSV original: {publicIndex.catalogSha256}</small></div>
    <CatalogSearch items={records} />
  </div>;
}
