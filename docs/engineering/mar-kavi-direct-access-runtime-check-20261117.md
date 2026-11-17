# MAR — correção de descoberta KAVI no site (17/11/2026)

## Evidência e hipótese
Usuário reportou ausência de KAVI em **qualquer** opção de "Unidade documental" na instância Streamlit pública. Não repetir instruções para procurar abas. O PR #101 já está em main com CI success, mas não há prova de que Streamlit Cloud esteja executando essa revisão e carregando o CSV/manifesto. Os testes existentes confirmam que no *repositório* o lote aprovado tem 200 fichas, hash verificado, links únicos e cobertura parcial. Não inferir estado do deploy sem telemetria.

## Contrato e risco
1. Criar rota de *apresentação* `?acervo=kavi` e botão **KAVI / Finna — acessar fichas**, visíveis em **qualquer** modo da UI, inclusive painel secundário. Evitar dependência de dropdown, filtro de vídeo ou cache de busca global. Não gerar novas fichas.
2. Carregar o índice KAVI exclusivamente com `load_published_kavi_rows(OUTPUT_DIR)`; rejeição de manifesto ou assinatura mantém **HOLD** e mensagem compreensível sem fallback para CSV.
3. Indicar no próprio site um marcador estático de versão da interface (`MAR-KAVI-DIRECT-20261117`), para distinguir aplicação atualizada de deploy antigo; não afirmar runtime SHA sem verificação. Mostrar contagem real do lote carregado (200 esperado, caso contrário indicar problema), e links de fichas de origem (nenhum player/download).
4. Link direto da ficha permanece no domínio HTTPS institucional, sem mídia reaproveitada. Explicitar que aprovação do índice de metadados não prova revisão individual nem autorização/reprodução de mídia.
5. Botão de retorno apenas muda o modo de visualização. Nenhum banco/Neon, cobrança, backup P0, coletor, API externa ou direitos de acesso são alterados.
6. Cache da pesquisa global não deve condicionar o modo de acesso direto. Para evitar sessão presa no modo antigo após atualização, reinicializar uma vez o modo principal por marcador de versão, preservando as demais preferências.

## Testes
- T1: rota e botão acessíveis sem selecionar corpus/filtros; contagem 200 com os arquivos publicados.
- T2: lote adulterado/incompleto gera HOLD, nunca exibe fichas não verificadas.
- T3: 200 IDs/URLs exclusivos, link apenas na origem, indicação explícita de status documental e reprodução não verificada.
- T4: teste de contrato garante que o marcador, `?acervo=kavi` e botão persistem e que coletores/P0 permanecem fora da alteração.
- T5: CI `quality` em HEAD do PR e pós-merge.

## Reversão
Reverter o PR (apenas código de apresentação e testes). Não editar dados publicados nem componentes de admissão científica. Implantação Streamlit Cloud ainda exige verificação real externa.
