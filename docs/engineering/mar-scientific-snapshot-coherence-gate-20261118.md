# MAR — Gate de coerência temporal dos snapshots (P0, 18/11/2026)

## Risco verificado
O Next.js usa output: export. O site carrega projeções versionadas em site/data (analytics, perfis institucionais, pesquisa, séries, inventário, casos, KAVI), enquanto a nuvem de palavras dispõe de gerador/PR próprios. Não existe ainda um gerador único, reproduzível e aprovado para **todas** as projeções. A simples implantação READY não significa sincronização com o estado científico.

## Mitigação inicial, NÃO solução integral
scripts/check_mar_scientific_snapshot_lock.py bloqueia, em CI, mudanças em qualquer insumo de pesquisa relevante ou projeção científica fora do baseline auditado em main a120102798467f67d8c9b8d905e1378e7b5fbf35. O arquivo site/data/scientific-snapshot-lock.json contém somente caminhos e identificadores Git de blob (não fichas, mídia, credenciais nem cursores). O teste é offline, determinístico e **somente leitura**. Um novo arquivo de corpus que corresponda aos padrões de entrada também falha.

**Limite essencial:** esta trava prova somente que os insumos e os JSONs estão iguais ao baseline, NÃO prova que o baseline era coerente, que o motor está atualizado, que as projeções foram geradas por código, ou que o site esteja autorizado a divulgar novos registros. A aprovação de um novo bundle requer reconstrução científica e revisão independente. Alterar hashes no lock sem prova de regeneração não é um procedimento de atualização válido.

A nuvem de palavras permanece com gerador separado, mas sua automação deve passar pelo gate ANTES de criar qualquer PR. Se um catálogo novo ou modificado surgir, o job falha em HOLD em vez de publicar apenas a nuvem. Arquivo de geometria é insumo cartográfico fixo, fora da projeção de corpus. A aprovação KAVI de 200 fichas é conferida em gate independente.

## Próxima etapa necessária: gerador completo, atômico e validado
1. Definir contrato versionado para cada projeção: lista fechada de insumos, esquema, unidade de contagem, datas, denominadores, direitos e gates de publicação. Registrar a matriz de dependências de todas as rotas.
2. Construir geradores determinísticos, sem rede, para analytics, perfis, temas, séries, comparações, inventário, casos e catálogo aprovado. Nenhuma nova ficha individual deve aparecer só por existir no CSV histórico. KAVI mantém exatamente 200 até aprovação específica.
3. Produzir um **bundle científico único** com epoch/snapshot ID, SHA-256 de cada insumo e saída, timestamp de origem e versão de código; gerar todos os arquivos em diretório temporário; validar esquema, contagens cruzadas, provas de origem e controles de publicação.
4. Testar inclusão sintética de um corpus, alteração de indicadores, falha parcial, dados adulterados, retrocesso temporal, HOLD, remoção de arquivo, regressão de URLs e rollback. Se qualquer teste falhar, **não publicar arquivo algum**.
5. Propor um PR único contendo bundle completo + manifesto + relatório de diffs; exigir CI e revisão humana, só então merge e build do mesmo commit no único projeto Vercel existente. Configurar Deployment Checks/branch protection para que Vercel não exponha builds inconsistentes.
6. Revalidar os painéis e os links com a mesma versão do bundle. Preservar o Streamlit, o SSO Vercel e todos os gates científicos até autorização explícita para abrir o acesso público.

## Não autorizado por este PR
- Não regenera nem altera dados científicos, hashes de fonte, fichas, direitos, mídia, Neon, Streamlit ou status HOLD.
- Não remove proteção de acesso, não cria projeto Vercel e não gera custos.
- Não declara a migração concluída, nem habilita novos corpora, nem garante que o deploy em produção esteja bloqueado por CI sem Deployment Checks.
