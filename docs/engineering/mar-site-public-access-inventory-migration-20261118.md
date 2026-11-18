# MAR — Migração do Índice de Dados Públicos (Streamlit → Next.js)

## Escopo executado
- Exportação de **60 linhas de corpora** no índice `observatorio_indice_dados_publicos_por_corpus.csv` e **3 unidades restritas adicionais** de `observatorio_unidades_acesso_restrito_indice.csv`, sem alterar os arquivos de origem.
- Rota estática `/indice-acesso/`, com pesquisa por instituição e filtros de histórico de acesso.
- Estado explícito de corpus identificado sem ficha exibida; motivo específico quando há evidência histórica e pendência documentada nos demais.
- Índice histórico de **194.057** registros materializados (165.134 classificados em superfície pública; 28.923 restritos), **não comparável diretamente** a direitos de republicação.
- Eye e Czech registram 7 fichas de exemplo acessadas como visitante comum; demais corpora mantêm `not_revalidated_in_this_migration`. APE mantém HOLD.
- A página não cria player, baixa mídia, executa coleta, importa fichas sem autorização, altera Neon, Streamlit ou os 200 registros KAVI.

## Limites metodológicos
"Disponível em superfície pública" no Streamlit histórico **não significa licença livre de republicação de descrições, imagens ou vídeo**. O levantamento foi observado sob regra de junho de 2026 e não comprova acesso atual de todas as rotas. Uma falha de API, DNS ou navegador não é ausência institucional de catálogo. Sem fundamento jurídico ou autorização científica, o corpus continua listado com motivo da não exibição, e não com alegação infundada de ilegalidade.

## Para expandir fichas individuais
Percurso humano na origem (G0/G1); documentar metadados, mídia e acesso em separado (G2); verificar direitos e termos por instituição; definir projeção factual mínima e licença quando aplicável; validação independente e inclusão admitida por corpus (G4). Só então mudar status de ficha pública e atualizar as rotas de modo auditável.

## CI e proteção
`MAR Next.js Site` verifica o JSON histórico, estados de publicação negada, integridade de KAVI, typecheck, build e rota estática. Este PR é independente do PR #105, que continua em HOLD para republicação individual de fichas Eye/Czech.

**Decisão:** inventário institucional público; novas fichas NÃO publicadas.
