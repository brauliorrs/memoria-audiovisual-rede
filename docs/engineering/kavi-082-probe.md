# Análise cumulativa nº 82 — KAVI / Elonet / Finna (sonda inicial)

## Escopo e estado

- Unidade: `fiaf-kavi` — Kansallinen audiovisuaalinen instituutti / National Audiovisual Institute, Finlândia.
- Issue: [#59](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59).
- **Estado: sonda técnica em avaliação; não incorporar nem avançar para nº 83.**
- Catálogo institucional publicamente indicado: [Elonet](https://elonet.finna.fi/Content/faq?lng=en-gb), serviço do KAVI integrado à Finna.
- Página oficial do KAVI: https://kavi.fi/en/film/
- Documentação oficial da [API Finna](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish).
- [Termos da API](https://www.kiwi.fi/spaces/Finna/pages/53839699/Finna%2BAPI%2BTerms%2Bof%2BUse): metadados CC0; mídias associadas e respectivos direitos não são automaticamente liberados.

## Critérios de prova

Elonet publica filmografia e serviços VOD. O instituto informa que a base inclui títulos cujo uso audiovisual **não pertence** ao KAVI. Por isso, três conjuntos não podem ser tratados como equivalentes: filmes catalogados, filmes preservados sob custódia do instituto e filmes disponíveis para visualização online.

A Finna documenta `/v1/search`, `facet[]` e, para grandes conjuntos, a paginação por `resumptionToken`. Também alerta que a paginação normal não é adequada para volumes altos. A presente sonda **não inicia coleta em lotes**: faz apenas testes públicos mínimos de disponibilidade e formato (facet `building` e amostra de título documentada), condicionados a verificação de `robots.txt` individual por host.

A etapa seguinte só poderá realizar enumeração em lotes quando identificar e demonstrar um filtro **oficial/documentado e reprodutível** que limite o conjunto a fichas da instituição KAVI, separando formato audiovisual de registros de biblioteca, autoridade e material não fílmico. A origem KAVI no índice não estabelece por si posse de direitos de vídeo.

## Protocolo da sonda

1. Avaliar `robots.txt` antes de qualquer consulta a `kavi.fi`, `elonet.finna.fi` e `api.finna.fi` (e novos hosts de redirecionamento separadamente).
2. Consultar as páginas oficiais de contexto e duas consultas pequenas e documentadas da API (facet com `limit=0`, busca de filme pelo título com `limit=2`).
3. Validar JSON, status, `resultCount`, identificadores não vazios e sem duplicação, faceta `building`, sem interpretar contagens de faceta como filme catalogado.
4. Proibir diretamente downloads de vídeos, filtros inferidos, IDs supostos, contorno de bloqueio, paginação massiva e incorporação automática.
5. Registrar por host/URL status, erro, evidência JSON, e gate fail-closed.

## Próximo gate

- Se API e Elonet forem acessíveis: investigar filtro exato do provedor, consulta somente de metadados com estrutura estável, `resumptionToken`, deduplicação, total reconciliado e amostras de fichas arquivísticas com proveniência.
- Se houver HTTP 403, challenge ou erro de `robots.txt`: registrar HOLD da superfície correspondente, sem contorno de proteção.
- Somente com enumeração **completa e verificável** e fichas semânticas comprovadas avançar a um staged collector de metadados.

## Reproduzir

```bash
python -m unittest discover -s tests -p 'test_kavi_elonet_probe.py' -v
python scripts/probe_kavi_elonet.py
```

Nenhum número de registros é afirmado antes da execução viva e exame de evidência.
