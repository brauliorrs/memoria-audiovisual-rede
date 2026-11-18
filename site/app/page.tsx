import Link from "next/link";
import { CatalogSearch } from "@/components/catalog-search";
import { TitleWordCloud } from "@/components/title-wordcloud";
import { publicIndex, records } from "@/lib/catalog";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="shell hero-inner">
          <div className="hero-copy">
            <p className="eyebrow eyebrow-light"><span className="live-dot" /> OBSERVATÓRIO CIENTÍFICO ABERTO</p>
            <h1>A memória audiovisual do mundo, <em>conectada.</em></h1>
            <p className="hero-description">Estude a circulação do audiovisual em rede: compare acervos, instituições e territórios, investigue condições de acesso e explore registros documentais na fonte original.</p>
            <div className="hero-actions">
              <Link className="button button-light" href="/observatorio/">Explorar o observatório <span aria-hidden="true">↗</span></Link>
              <Link className="button button-outline" href="/temas/">Explorar temas e territórios <span aria-hidden="true">→</span></Link>
            </div>
          </div>
          <div className="hero-visual hero-wordcloud">
            <TitleWordCloud />
          </div>
        </div>
      </section>
      <section className="numbers">
        <div className="shell numbers-grid">
          <div><span className="number">{publicIndex.total}</span><span className="number-label">Fichas KAVI no índice público</span></div>
          <div><span className="number">1</span><span className="number-label">Fonte com fichas neste MVP</span></div>
          <div><span className="number">100%</span><span className="number-label">Links para registros na origem</span></div>
          <div><span className="number">0</span><span className="number-label">Mídias hospedadas pelo MAR</span></div>
        </div>
      </section>
      <section className="shell intro-section">
        <div className="section-intro">
          <div><p className="eyebrow">PESQUISA DOCUMENTAL</p><h2>Explore o acervo publicado</h2></div>
          <p>A análise integrada das instituições e a comparação entre corpora estão disponíveis no Observatório. O catálogo de fichas documentais permanece restrito às fontes com admissão comprovada.</p>
        </div>
        <CatalogSearch items={records} />
      </section>
      <section className="principles-band">
        <div className="shell principles-inner">
          <div><p className="eyebrow eyebrow-light">NOSSO COMPROMISSO</p><h2>Conectar sem apropriar.</h2></div>
          <div className="principles-list">
            <p><span>01</span> Fichas e links permanecem associados à instituição de origem.</p>
            <p><span>02</span> Publicação de metadados não equivale a validação de reprodução ou direitos.</p>
            <p><span>03</span> Cada expansão depende de evidências e revisão documentada.</p>
          </div>
        </div>
      </section>
    </>
  );
}
