# MAR — Arquitetura B2: revisão de bundle científico estático (19/11/2026)

**Status:** proposta em PR rascunho empilhado sobre B1 (#123) e trava preventiva (#121). Não há autorização de ingestão, implantação, acesso público ou publicação de fichas.

## Risco e objetivo
O Next.js pode continuar como exportação estática sem perder atualização científica, contanto que todas as projeções relevantes sejam geradas e liberadas com a mesma versão dos insumos. Nunca confundir saída de coleta, análise, validação e aprovação de publicação. O corpus em HOLD não pode adquirir uma ficha individual pelo simples fato de um JSON ter sido gerado.

## Entrega experimental desta etapa
- O script scripts/build_mar_site_bundle_b2.py aplica a trava read-only do PR #121 aos 563 insumos versionados e aos 33 JSONs científicos do site.
- Verifica B1 (62 relatórios), cobertura de corpora dos recortes de temas, países, plataformas e séries, quantidades e IDs de instituições. Não reutiliza mídia nem expõe dados individuais de terceiros.
- Confere que o Índice de Dados Públicos não autoriza fichas, que casos documentais não se tornaram publicação, que KAVI mantém 200 fichas de metadados aprovadas e que a nuvem de palavras não divulga títulos individuais.
- Define um epoch SHA-256 determinístico para os insumos e as 34 saídas consideradas (33 projeções mais nuvem); escreve manifesto com hashes individuais, commit de baseline e publicação explicitamente não autorizada.
- Modo de checagem não escreve no repositório. O staging só é permitido em diretório novo e fora do repositório; grava em pasta temporária e faz rename atômico, sem substituir a versão anterior.
- Os testes sintéticos garantem falha segura quando um corpus não aprovado é acrescentado ou um relatório é adulterado; verificam imutabilidade do site existente, inexistência de pacote parcial após erro e determinismo do manifesto.

## Limite crítico
**O gerador integral B2 AINDA NÃO ESTÁ CONCLUÍDO.** Este PR implementa um envelope de revisão e travas sobre o baseline histórico; não reconstrói automaticamente todos os JSONs e ainda não demonstra a incorporação positiva de corpus validado em todos os indicadores. Os testes de corpus sintético comprovam bloqueio, não admissão positiva. O manifesto não autoriza publicação.

## Gates seguintes
1. Projetores completos e determinísticos para recortes, instituições, mapas, inventário, casos e índice; aspectos sujeitos a revisão humana continuam sem regeneração automática.
2. Admissão positiva de um corpus sintético aprovado somente para agregados; teste de todos os diffs, epoch, privacidade, publicação e rollback.
3. Build estático por versão única, revisão de PR, CI e bloqueio real de promoção Vercel antes da aprovação. A CI sozinha não prova bloqueio de implantação.
4. Fechamento da paridade Streamlit/Next.js e continuidade do fechamento europeu antes de abrir o acesso ao público.

Nenhuma modificação de dados científicos, SSO, Neon, Streamlit, mídia, domínio Vercel, custos ou corpora sob HOLD.
