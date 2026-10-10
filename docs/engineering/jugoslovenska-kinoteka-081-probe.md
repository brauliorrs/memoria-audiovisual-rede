# Análise cumulativa nº 81 — Jugoslovenska Kinoteka (sonda inicial)

## Escopo, proveniência e status

- Unidade: `fiaf-jugoslovenska-kinoteka` (FIAF, Sérvia).
- Sítio institucional: https://www.kinoteka.org.rs/
- Subdomínio em inglês: https://en.kinoteka.org.rs/
- Issue do ciclo: https://github.com/brauliorrs/memoria-audiovisual-rede/issues/57
- PR técnico: https://github.com/brauliorrs/memoria-audiovisual-rede/pull/58
- **Estado da superfície institucional: HOLD / não incorporada.**
- **Estado da análise nº 81: aberto** para auditoria de superfícies subordinadas externas oficialmente referenciadas.

## Superfície institucional auditada

O domínio oficial apresenta o arquivo de filmes, com mais de 100 mil cópias, e informa uma catalogação em suporte tradicional e digital; esse inventário físico não se confunde com uma enumeração web de fichas patrimoniais.

O site publica uma lista identificável de 100 filmes sérvios declarados patrimônio cultural de grande importância, em https://www.kinoteka.org.rs/srpski-igrani-filmovi-1911-1999-100-najboljih/. Esse material é uma lista de títulos/anos/diretores, não fichas arquivísticas individuais que comprovem exemplares sob custódia, identificadores de acervo ou completude do catálogo online.

A sonda obedece às seguintes portas: `robots.txt` individual por domínio HTTPS, apenas sitemaps explicitamente declarados ou apresentados no HTML, contêineres de XML como fonte de papéis (não o sufixo da URL), rejeição de `loc` sem contêiner, separação correta de `image:loc`, gzip com limite de descompressão, URLs exatas sob hosts autorizados, sem IDs supostos e sem download de mídia.

### Execução viva reproduzível

Artefato do GitHub Actions `jugoslovenska-kinoteka-probe`, id `11681554889`, digest ZIP `sha256:d1d07fa04bd9c3bb0bc820ece64f2aac5e9a48e0976f86087c31b22310a165e8`, HEAD `e05260131b3dbb8c2ba5bf2adba53b2efa1d0238`.

| Indicador | Valor |
| --- | ---: |
| Domínios cujas regras `robots.txt` foram avaliadas | 2 (www e en) |
| Índices de sitemap descobertos | 2 |
| Sitemaps filhos percorridos | 12 |
| URLs públicas distintas enumeradas | 1.496 |
| Erros/truncamento de enumeração | 0 |
| Postagens (sitemaps post) | 1.205 |
| Páginas (sitemaps page) | 22 |
| Portfolio | 234 |
| Categorias/tags/autores | 35 |
| URLs reconhecidas como programação pelo classificador | 272 |
| Lista patrimonial dos 100 filmes | 1 página |
| URLs não classificadas semanticamente só pelo path | 1.177 |
| Páginas da amostra semântica estratificada | 20 |
| Páginas HTTP 200 da amostra | 20 |
| Fichas individuais com evidência estruturada de identificador de custódia | 0 |

SHA-256 da lista ordenada de URLs:
`549c24f93ba9e4159abac8cb1a1fc0966fc3bdfd9aabb8b974db727db86ccced`.

A amostra cobriu postagens e páginas em sérvio e inglês, e quatro páginas do tipo `portfolio`. Os exemplos auditados de `portfolio` são programação, temporadas e retrospectivas, sem fichas individuais de custódia.

Gate técnico retornado: `hold_no_verified_public_archival_records`; `staged_collector_authorized=false`. **HOLD não significa inexistência de filmes nem prova exaustiva de ausência de um catálogo fora da superfície encontrada.** Significa que o protocolo de incorporação não encontrou fichas de filmes sob custódia enumeráveis com evidência suficiente nas superfícies públicas auditadas.

## Superfícies subordinadas relevantes, ainda não adjudicadas

O próprio arquivo informa que materiais dos seus fundos são apresentados em https://www.kinoteka.org.rs/filmovi-iz-fonda-kinoteke-na-internetu/: trechos no canal YouTube oficial, publicações na conta Vimeo e filmes da Primeira Guerra Mundial vinculados ao European Film Gateway (EFG). Esses materiais não devem ser misturados com a listagem de programação nem transformar o acervo de toda a plataforma externa em acervo de Kinoteka.

**Próximo gate nº 81:** verificar acesso público, robots e mecanismo reprodutível de enumeração da coleção publicada pelo arquivo no EFG, exigir campo de provedor/custódia por registro, metadados semânticos de item audiovisual e distinguir trechos de itens integrais. Usar APIs somente quando documentalmente públicas, sem inferir IDs, sem contornar barreiras e sem capturar mídia. Se não houver rota admissível, protocolar HOLD formal e avançar a fila somente depois disso.

## Comandos

```bash
python -m unittest discover -s tests -p 'test_jugoslovenska_kinoteka_probe.py' -v
python scripts/probe_jugoslovenska_kinoteka.py
```

Os resultados acima são da sonda viva. O merge da análise e eventual transição histórica da fila não estão autorizados por este documento; ficam condicionados aos gates restantes.
