import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { publicIndex, records } from "@/lib/catalog";

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return records.map((record) => ({ id: record.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const record = records.find((item) => item.id === id);
  if (!record) return { title: "Ficha não encontrada" };
  return {
    title: record.title + " — KAVI / Finna",
    description: "Ficha documental publicada no MAR: " + record.title + ". Metadados de origem, proveniência e situação de validação.",
  };
}

export default async function KaviRecordPage({ params }: Props) {
  const { id } = await params;
  const record = records.find((item) => item.id === id);
  if (!record) notFound();

  const fields = [
    ["Identificador na origem", record.id],
    ["Ano informado", record.year ?? "Não informado"],
    ["Gêneros", record.genres || "Não informados"],
    ["Assuntos", record.subjects || "Não informados"],
    ["Idioma (código original)", record.languages || "Não informado"],
    ["Instituição de referência", record.institution],
    ["País", record.country],
    ["Serviço de origem", record.source],
  ];

  return (
    <div className="shell page-shell record-detail">
      <nav aria-label="Caminho da ficha" className="record-breadcrumb">
        <Link href="/acervo/">Acervo</Link><span aria-hidden="true">/</span>
        <Link href="/instituicoes/kavi/">KAVI / Kuvi</Link><span aria-hidden="true">/</span>
        <span aria-current="page">Ficha documental</span>
      </nav>
      <p className="eyebrow">REGISTRO DOCUMENTAL · FINNA / ELONET</p>
      <h1>{record.title}</h1>
      <p className="page-lede">Ficha de metadados publicada em índice parcial, associada a uma instituição de referência. Esta página não disponibiliza nem verifica a reprodução do filme.</p>
      <div className="record-detail-grid">
        <section aria-labelledby="ficha-dados" className="detail-panel">
          <h2 id="ficha-dados">Metadados da ficha</h2>
          <dl className="metadata-list">
            {fields.map(([label, value]) => (
              <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
            ))}
          </dl>
          <a className="button button-dark detail-source-link" href={record.sourceUrl} target="_blank" rel="noopener noreferrer">
            Abrir ficha na Finna ↗
          </a>
          <p className="detail-external-note">Você será encaminhado para o registro no serviço de origem.</p>
        </section>
        <aside className="detail-panel detail-provenance" aria-labelledby="ficha-proveniencia">
          <h2 id="ficha-proveniencia">Proveniência e validação</h2>
          <p className="document-pill">Metadados publicados · cobertura parcial</p>
          <dl className="metadata-list">
            <div><dt>Revisão científica individual</dt><dd>Não concluída</dd></div>
            <div><dt>Reprodução pública do vídeo</dt><dd>Não verificada</dd></div>
            <div><dt>Direitos e custódia da mídia</dt><dd>Não verificados</dd></div>
            <div><dt>Índice de referência</dt><dd>KAVI/Finna · {publicIndex.total} fichas</dd></div>
            <div><dt>Data de observação</dt><dd>{publicIndex.observedOn}</dd></div>
          </dl>
          <p className="provenance-hash"><strong>SHA-256 do catálogo aprovado</strong><code>{publicIndex.catalogSha256}</code></p>
        </aside>
      </div>
      <p className="detail-bottom-link"><Link href="/instituicoes/kavi/">← Voltar ao catálogo KAVI</Link></p>
    </div>
  );
}
