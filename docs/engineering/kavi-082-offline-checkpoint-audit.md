# KAVI #82 — auditoria offline de checkpoints Finna (incremento posterior ao PR #62)

## Objetivo e delimitação

O incremento acrescenta `scripts/audit_kavi_finna_staging.py` para **auditar localmente** um lote de metadados já materializado pelo executor staged existente. Não cria coletor paralelo, não consome a API, não baixa mídia, não publica identificadores nem promove dados ao corpus MAR. Reutiliza exatamente o replay de integridade de `metadata_staging._restore`, o `FileWriteLock` e a auditoria de proveniência/normalização comprovada no ensaio vivo de duas páginas do PR #62.

O PR #62 já comprovou 400 registros em 2 páginas da Finna, com `resumptionToken` válido, sem incorporação de mídia. Isso **não demonstra** capacidade de recuperar integralmente 138.379 registros ou validade indeterminada do token; a fonte é dinâmica, com contagem observada diferente entre execuções anteriores (138.377 e 138.379). A documentação pública [Finna API](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish) prevê `resumptionToken`, mas a continuidade longa, expiração, taxa admissível e estabilidade do snapshot ainda não estão comprovadas para o lote integral.

## Contrato verificável

1. A auditoria recebe de fora do checkpoint o `evidence_sha256` previamente validado e o `expected_total` observado no preflight autorizado. **Não confia no total ou no escopo declarados pelo próprio checkpoint para definir a âncora.**
2. Adquire o mesmo lock da rotina staged, lê localmente o checkpoint, recalcula o hash do escopo aprovado e reexecuta todas as verificações dos brutos endereçados por SHA-256, IDs, cadeia de cursores, totais, duplicidade, estado parcial/completo e flags obrigatórias de bloqueio.
3. Revalida identidade e ordem de IDs da resposta original versus registros normalizados, código do provedor KAVI, classificação exploratória dos filmes, formatos observados e estado conservador de custódia/licença. Falhas são rejeitadas sem tentar consertar dados, avançar páginas ou inferir direitos.
4. Emite **somente** sumário público de contagens, hashes agregados, classificações e códigos de falha. Tokens, identificadores de ficha, URLs de mídia e conteúdos brutos permanecem no staging local excluído do Git.
5. O status `complete` de um checkpoint significa apenas que **aquela paginação** terminou com contagens consistentes. Nunca autoriza publicação, não certifica estabilidade do índice, custódia KAVI ou direitos de mídia.

A auditoria é offline: `api_snapshot_freshness_verified=false` em todas as saídas, `promotion_authorized=false` e `media_downloaded=false`. Não é necessário nem permitido criar uma chamada à API nesse comando. O lock cooperativo `run.lock` é criado e removido localmente para evitar corrida com outra execução do staging.

## Como operar sem disparar nova coleta

Executar de dentro da raiz do repositório, com o mesmo diretório local previamente produzido e com âncoras registradas fora dele:

```bash
python scripts/audit_kavi_finna_staging.py \
  --directory data/staging/kavi-finna \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049 \
  --expected-total 138379
```

O total no exemplo é **histórico**, observado no ensaio vivo de outubro de 2026. Só deve ser usado se corresponder ao preflight específico do checkpoint local a auditar. Para novos lotes, a contagem deve vir de evidência externa ao checkpoint. Desalinhamento: **HOLD/rejeição**, sem ajustar manualmente hashes, total ou cursor. O comando retorna código de saída 2 na rejeição.

## Gating para enumeração integral

Antes de ampliar o volume além do ensaio de duas páginas:

- Pré-registrar no protocolo de execução o denominador/instante do preflight, as condições de expiração do token, armazenamento e durabilidade do checkpoint, quota de páginas, atraso interlotes, erro/retentativa e interrupção em mudanças no índice.
- Confirmar por evidência oficial ou teste limitado que o cursor não perde continuidade em operações longas, especialmente ao retomar processos; não substituir cursores por IDs estimados nem contornar robots.
- Executar coleta apenas em lotes pequenos e explicitamente autorizados pelo operador, separados da CI. A auditoria offline deve ocorrer após cada lote, independentemente do sucesso HTTP.
- Após término verificável, preparar amostragem determinística e revisão humana por ficha de proveniência, custódia e direitos, antes de considerar qualquer gate de promoção.

**Decisão:** a issue #59 / análise #82 permanece aberta; não iniciar a análise #83 e não conectar o staging a `IngestionCoordinator`, corpus ativo ou distribuição de mídia.

## Testes sem rede

```bash
python -m unittest discover -s tests -p 'test_kavi_finna_offline_audit.py' -v
python -m unittest discover -s tests -p 'test_kavi_finna_two_page_resume.py' -v
```

O `Quality Checks` também executa a suíte integral de `unittest`.
