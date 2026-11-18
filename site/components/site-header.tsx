import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="shell header-inner">
        <Link className="brand" href="/" aria-label="MAR — início">
          <span className="brand-mark" aria-hidden="true">
            <span className="brand-mark-center" />
          </span>
          <span className="brand-name">
            <strong>MAR<span className="brand-dot">.</span></strong>
            <small>Memória Audiovisual em Rede</small>
          </span>
        </Link>
        <nav aria-label="Menu principal" className="main-nav">
          <Link href="/observatorio/">Observatório</Link>
          <Link href="/analises/">Análises</Link>
          <Link href="/acervo/">Explorar acervo</Link>
          <Link href="/instituicoes/">Instituições</Link>
          <Link href="/indice-acesso/">Índice de acesso</Link>
          <Link href="/casos/">Casos</Link>
          <Link href="/metodologia/">Metodologia</Link>
        </nav>
        <Link className="header-action" href="/acervo/">Abrir catálogo <span aria-hidden="true">↗</span></Link>
      </div>
    </header>
  );
}
