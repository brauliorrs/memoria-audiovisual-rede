import type {Metadata} from "next";
import {DocumentedCases} from "@/components/documented-cases";
import cases from "@/data/documented-cases.json";
export const metadata:Metadata={title:"Casos documentados — Pesquisa em audiovisual"};
export default function CasesPage(){return <main className="shell page-shell">
<p className="eyebrow">METODOLOGIA · FONTES DOCUMENTADAS</p>
<h1>Casos documentados de acesso</h1>
<p className="page-lede">O audiovisual em rede inclui instituições cujo acervo foi identificado, mesmo quando o catálogo não é acessível integralmente. Estes {cases.cases.length} estudos de caso registram obstáculos, evidências e caminhos de investigação, migrados do Streamlit.</p>
<DocumentedCases/>
</main>;}
