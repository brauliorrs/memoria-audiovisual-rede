import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Metodologia" };
export default function MethodologyPage() {
  return <div className="shell page-shell methodology">
    <p className="eyebrow">CRITÉRIOS CIENTÍFICOS</p>
    <h1>Uma plataforma para pesquisar, não apropriar.</h1>
    <p className="page-lede">O MAR organiza fichas e fontes documentais com rastreabilidade. Publicar um registro não significa disponibilizar um filme nem validar direitos autorais.</p>
    <div className="method-rows">
      <article><span>01</span><div><h2>Proveniência verificável</h2><p>Metadados publicados por conjuntos aprovados e associados a uma origem institucional identificável. O índice inicial KAVI possui manifesto com SHA-256.</p></div></article>
      <article><span>02</span><div><h2>Aprovação documental independente</h2><p>O motor de coleta, o banco de auditoria e a autorização científica são domínios diferentes. Nenhuma inserção técnica aprova automaticamente a publicação de um corpus.</p></div></article>
      <article><span>03</span><div><h2>Link de origem, sem hospedagem de mídia</h2><p>O MAR direciona para fichas institucionais externas. Não incorpora vídeos, não baixa filmes e não afirma que um link documental oferece reprodução pública.</p></div></article>
      <article><span>04</span><div><h2>Expansão controlada</h2><p>Novas instituições e registros entram no índice somente após verificação de evidências, deduplicação e manifestação de autorização. Fontes bloqueadas permanecem fora do catálogo público.</p></div></article>
    </div>
    <div className="method-cta"><p>Consulte os metadados publicados e examine as fichas na origem.</p><Link className="button button-dark" href="/acervo/">Explorar o catálogo ↗</Link></div>
  </div>;
}
