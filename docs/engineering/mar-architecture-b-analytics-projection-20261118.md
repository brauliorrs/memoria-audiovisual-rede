# MAR — Decisão de arquitetura B e primeiro projetor de relatórios (B1)

**Status:** implementação inicial em PR empilhado; **não integrada à main, não autorizada para publicação**. Regra do usuário: acesso público ao Vercel apenas depois da migração completa e da preparação para incorporar novos corpora.

## Decisão

- **Escolhida:** Python científico e `data/output` seguem como fonte de verdade; projeções por Python alimentam o Next.js com `output: export`, mantendo o projeto Vercel existente.
- **Rejeitada:** trocar apenas o diretório de saída dos CSVs do Streamlit; não resolve formatos, coerência nem política de divulgação.
- **Adiada:** migração imediata para API dinâmica/Neon, sem demonstração de necessidade e sem gates P0 de armazenamento.
- **Disponibilidade:** Streamlit preservado, Vercel protegido; nenhuma mudança de autenticação, banco, mídia, custos ou corpus.

## B1 implementado neste PR

`scripts/build_mar_site_analytics.py` reconstrói **apenas os 62 relatórios agregados** (seis arquivos `analytics-0.json` ... `analytics-5.json`) a partir de `data/output/<corpus>_relatorio.json`. Campos permitidos: código, arquivo de origem, contagem de instituições e vídeos/embeds e mapas agregados de integridade, status, plataforma e continentes. Descarta `top_institutions`, URLs de mídia e detalhes de itens. Nunca consulta a internet ou banco.

O comando `--check` compara **os valores** com os JSONs estáticos atuais, falhando diante de qualquer divergência ou fonte ausente/nova, mesmo quando o parser de JSON aceita formatação diferente. Um relatório recém-adicionado **não** é promovido implicitamente: a lista de corpora do conjunto já revisado precisa ser reconciliada em um PR científico específico.

`--stage-dir /caminho/fora/do/repo` gera somente um candidato de revisão em diretório novo, com hashes SHA-256 dos insumos e resultados, status `REVIEW_ONLY_NOT_PUBLICATION_AUTHORIZATION`. O comando recusa gravar dentro do repositório e recusa substituir dados existentes. Nenhum JSON do site nem o arquivo de controle do PR #121 é alterado.

`tests/test_mar_site_analytics_projector.py` cobre baseline, deriva, corpus inédito, corpus ausente, JSON inválido, contadores incorretos, exclusão de detalhes individuais, manifesto e segurança de estágio.

A CI `MAR Next.js Site` verifica B1 **antes** do build estático. Ela não habilita ingestão, não resolve o gate científico de publicação, e não transforma o snapshot histórico em evidência atual. Este PR depende da primeira trava preventiva PR #121.

## Próximos contratos B2/B3

1. Projetar `research-slices`, `research`, `institution-profiles`, inventário de acesso, casos documentados, nuvem e fichas individuais autorizadas, cada um com contrato e aprovação de escopo; separar os artefatos geográficos de referência dos dados científicos.
2. Introduzir manifesto de **bundle integral** com epoch, SHA-256, insumos, versão de regras, conjunto de corpora, decisões de aprovação e referência de commit. Gerar todos os JSONs em staging protegido, validar paridade de contagens, autorizações e links, e publicar o conjunto em um único commit/PR após revisão.
3. Criar teste de um corpus sintético admitido, alteração de dado, corpus HOLD, regressão e falha/rollback; configurar gates de deploy no Vercel para que a produção não avance antes do CI completo.
4. Concluir paridade funcional Streamlit → site e fechamento europeu. **Só no último passo**, após autorização expressa, abrir o site ao público.

**Proibições:** auto-admissão de arquivos, mudança nos 200 KAVI, reprodução ou download de mídia, exposição de HOLD, escrita em Neon, desbloqueio SSO, novas despesas no MVP.
