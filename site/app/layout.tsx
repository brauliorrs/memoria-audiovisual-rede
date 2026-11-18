import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "MAR — Memória Audiovisual em Rede",
    template: "%s | MAR",
  },
  description: "Observatório aberto da memória audiovisual: metadados institucionais, rastreabilidade, pesquisa e acesso às fichas na origem.",
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <a className="skip-link" href="#conteudo">Ir para o conteúdo</a>
        <SiteHeader />
        <main id="conteudo">{children}</main>
        <footer className="footer">
          <div className="shell footer-grid">
            <div>
              <strong>MAR<span className="brand-dot">.</span></strong>
              <p>Memória Audiovisual em Rede</p>
              <span>Pesquisa, proveniência e acesso público responsável.</span>
            </div>
            <div className="footer-links">
              <Link href="/acervo/">Acervo</Link>
              <Link href="/instituicoes/">Instituições</Link>
              <Link href="/metodologia/">Metodologia científica</Link>
              <a href="https://github.com/brauliorrs/memoria-audiovisual-rede" target="_blank" rel="noopener noreferrer">Código e auditoria ↗</a>
            </div>
          </div>
          <div className="shell footer-bottom">
            <span>Índice público experimental · apenas metadados aprovados</span>
            <span>Não hospeda filmes, reproduções ou arquivos audiovisuais.</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
