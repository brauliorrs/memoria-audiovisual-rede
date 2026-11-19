import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "@/components/site-header";
import { LocaleProvider, LocalizedText } from "@/components/site-locale";
import {InstitutionalText} from "@/components/institutional-copy";
import {PUBLIC_ORIGIN} from "@/lib/seo";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase:new URL(PUBLIC_ORIGIN),
  applicationName:"MAR — Memória Audiovisual em Rede",
  openGraph:{type:"website",siteName:"MAR — Memória Audiovisual em Rede",locale:"pt_BR"},
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
        <LocaleProvider>
        <a className="skip-link" href="#conteudo"><InstitutionalText id="skipContent"/></a>
        <SiteHeader />
        <main id="conteudo">{children}</main>
        <footer className="footer">
          <div className="shell footer-grid">
            <div>
              <strong>MAR<span className="brand-dot">.</span></strong>
              <p>Memória Audiovisual em Rede</p>
              <span><LocalizedText id="sourceNote" /></span>
            </div>
            <div className="footer-links">
              <Link href="/acervo/"><LocalizedText id="navCatalog"/></Link>
              <Link href="/instituicoes/"><LocalizedText id="navInstitutions"/></Link>
              <Link href="/metodologia/"><LocalizedText id="navMethod"/></Link>
              <a href="https://github.com/brauliorrs/memoria-audiovisual-rede" target="_blank" rel="noopener noreferrer"><InstitutionalText id="footerCode"/> ↗</a>
            </div>
          </div>
          <div className="shell footer-bottom">
            <span><LocalizedText id="historicalWarning"/></span>
            <span><InstitutionalText id="footerNoMedia"/></span>
          </div>
        </footer>
        </LocaleProvider>
      </body>
    </html>
  );
}
