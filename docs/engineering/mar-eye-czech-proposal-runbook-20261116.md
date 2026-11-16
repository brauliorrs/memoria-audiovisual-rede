# MAR — execução operacional de propostas Eye/Czech (somente revisão)

O pipeline está no PR #97, **empilhado sobre PR #96**. PR #95 contém o leitor de publicação separado. Nenhuma destas branches publica automaticamente na `main`.

## Evidências necessárias (NÃO estão no repositório nesta etapa)

Uma captura de sonda pública autorizada, com data, URL institucional, limites de páginas e a resposta já normalizada pelos parsers existentes. O JSON deve ficar em um diretório privado, fora do repositório, sem tokens, cookies, headers de autenticação, bytes de mídia ou links diretos para streams. A autoridade da fonte, a atualidade, `robots.txt`, termos e consentimento de consulta devem ser confirmados no momento da sonda, não inferidos pelo SHA.

### Eye (uma ou duas páginas previamente autorizadas)

A evidência deve ter estrutura:

```json
{
  "corpus": "eye",
  "sample_complete": false,
  "records": [
    {
      "record_id": "slug-verificado-da-origem",
      "page_url": "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/slug-verificado-da-origem",
      "title": "Título efetivamente retornado pela origem",
      "subject": "",
      "description": "",
      "date": ""
    }
  ]
}
```

**Exemplo de estrutura, não evidência real.** O código exige de 1 a 100 fichas, URL institucional segura e ID não repetido. O CSV de 630 fichas já existente é a baseline. `changed` exige análise de atualização do legado em outro fluxo, `not_observed` jamais equivale a remoção.

### Czech (um programa e um episódio previamente autorizados)

O JSON deve conter `corpus="czech"` e `episode` com `record_id`, `page_url` institucional, `title`, `subject`, `description`, `date` e `embedded=true`, **somente se** extraído pelo parser da resposta e sustentado pela captura da origem. É apenas sinal técnico registrado, não confirmação presente de playback ou direitos.

## Procedimento de preparação — sem promoção

1. Guardar a evidência JSON imutável fora do repositório e registrar um SHA-256 auditado independentemente (no Windows: `Get-FileHash caminho.json -Algorithm SHA256`).
2. Com a branch do PR #97 checkoutada e dependências instaladas, executar a geração local:

```powershell
python -m scripts.build_eye_czech_review_proposal eye --evidence-file C:\MAR-privado\eye.json --evidence-sha256 SHA64 --output-dir C:\MAR-revisao\eye-proposta-nova
python -m scripts.build_eye_czech_review_proposal czech --evidence-file C:\MAR-privado\czech.json --evidence-sha256 SHA64 --output-dir C:\MAR-revisao\czech-proposta-nova
```

3. Conferir `eye.candidate.csv` / `czech-television.candidate.csv` e o `*.proposal.json`. Os CSVs usam exatamente o esquema de 12 campos do PR #95, porém o estado é `pending_independent_review`; por desenho, **não são admissíveis** por aquele leitor.
4. Solicitar revisão de identidade, links, direitos, origem, escopo e rastreabilidade a revisor independente. Somente após decisão humana, criar PR específico para o lote aprovado, com seu novo CSV e manifesto SHA-256, prova verificável de execução e `record_review_status=approved_metadata_only`. Esse passo não possui automação neste PR.
5. Nunca mover diretamente o CSV pendente para `data/output/mar_admitted`, nem alterar flags de aprovação só para satisfazer o validador.

O gerador falha em modo HOLD quando a evidência não existe, a integridade diverge, a URL é irregular, os IDs são duplicados ou o diretório de saída já existe. A saída de revisão deve ficar **fora de todo o repositório**. Não foi acionado nenhum coletor, banco, backup ou cron por esse fluxo.
