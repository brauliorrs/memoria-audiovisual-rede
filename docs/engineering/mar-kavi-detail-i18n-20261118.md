# MAR — Internacionalização das 200 fichas individuais KAVI

**Etapa:** 18/11/2026. **Destino:** único projeto Vercel `mar-public-site`, no domínio `https://mar-public-site.vercel.app/`. **Origem científica:** catálogo KAVI/Finna com metadados já aprovados para publicação parcial.

## Entrega

A rota estática `/acervo/kavi/[id]/` continua gerando exatamente as **200 páginas aprovadas**, sem alterar os identificadores, os links de origem, os títulos, o schema científico ou os dados de origem. Os metadados SEO continuam usando o título exato da obra, sem tradução artificial.

O corpo da ficha é o componente `site/components/kavi-record-detail.tsx`, que usa o seletor existente `useSiteLocale()` e o dicionário editorial `site/components/scientific-i18n.tsx`. Em **português, inglês e espanhol**, traduz:

- navegação e contexto da ficha;
- rótulos de ID, ano, gêneros, assuntos, idioma, instituição, país e origem;
- avisos de campos ausentes, sem criar valores;
- botão para consultar a fonte oficial Finna e aviso de navegação externa;
- proveniência, índice de 200 fichas, data da observação e SHA-256 do catálogo aprovado;
- revisão científica individual **não concluída**, reprodução pública **não verificada**, e direitos/custódia da mídia **não verificados**.

**Apenas os rótulos e as explicações editoriais são traduzidos.** Os valores de metadados originais (`record.title`, `record.id`, `record.year`, `record.genres`, `record.subjects`, `record.languages`, `record.institution`, `record.country`, `record.source`, `record.sourceUrl`) são exibidos literalmente. Não se disponibiliza player, mídia, miniaturas, download, incorporação, crawler ou conexão com Neon.

## Guardrails e validação

- `generateStaticParams` continua derivando IDs do índice KAVI aprovado.
- O servidor localiza o registro, define metadata SEO e passa somente o registro e valores pequenos do manifesto ao componente interativo (não passa todos os 200 itens ao cliente).
- O componente nunca acessa banco, API externa ou fontes HOLD; a tradução não amplia o universo dos registros publicados.
- `site/tests/kavi-record-detail.test.cjs` renderiza um registro real nos três idiomas e verifica título, valores documentais, URL Finna, SHA, data e avisos; testa também um registro com campos ausentes.
- `tests/test_mar_kavi_detail_i18n.py` verifica a permanência dos 200 registros, o escopo do manifesto e a ausência de mídias e de incorporação.
- A CI `MAR Next.js Site` executa esses contratos antes da tipagem, do build estático e da contagem de 200 rotas.

## Limitações preservadas

A internacionalização é **da interface**, não do documento de origem. Políticas jurídicas de terceiros, categorias de assunto e nomes próprios permanecem na forma registrada. Metadados SEO e links específicos por idioma, auditoria visual em celulares e revisão humana de eventuais traduções documentais ainda são futuras etapas. O Streamlit e as portas de autorização científica permanecem inalterados.
