# MAR — Dossiê de admissibilidade documental: Czech Television

**Versão:** minuta técnica 2026-11-18  
**Decisão vigente:** HOLD — **NÃO É UMA AUTORIZAÇÃO**  
**Escopo:** somente metadados textuais e links de origem; nenhuma licença presumida para mídia, cópia, player ou captura.

## Evidência interna
- Fonte histórica: `data/output/czech_tv_catalogo_videos_analitico.csv`.
- SHA-256 confirmado em CI: `eeea2152efdce800cefb2587c35500a6913a86d93e1b951460c16e6f14eaf1eb`.
- Linhas auditadas: **10**; URLs oficiais sintaticamente válidas e distintas: **10**.
- IDs derivados e distintos: **10**.
- Duplicatas exatas, equivalências de URL, colisões de ID, conflitos de título, divergências institucionais detectadas: **zero**.
- Auditoria offline: https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/44361604953
- Artefato auditável (retenção 30 dias): https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/44361604953/artifacts/14456100644

## Evidência externa
- Fichas documentais amostradas e localizadas: 7/7, em 18/11/2026.
- Evidências individuais: `docs/engineering/mar-multicorpus-expanded-sample-20261118.md`.
- A verificação externa foi intencional e não probabilística; não representa os 10 registros.
- Separar data do episódio ou de publicação do ano de produção da obra.
- A amostra contempla diferentes séries e tipos documentais.


## Verificação de políticas institucionais (18/11/2026)
- https://www.ceskatelevize.cz/vse-o-ct/spoluprace/archiv-ct/co-delame/: arquivo declara acesso a pesquisadores e trabalho de descrição, correção e organização de metadados. Acesso para pesquisa não é licença de republicação dos metadados.
- https://www.ceskatelevize.cz/vse-o-ct/jak-sledovat/napoveda-k-internetovemu-vysilani/: a reprodução de programas no iVysílání está sujeita a direitos e limitações variáveis; estes direitos não devem ser confundidos com direitos sobre dados descritivos.
- https://www.ceskatelevize.cz/vse-o-ct/english/production-services/: licenciamento de conteúdo audiovisual tratado por setores específicos. Não é uma autorização de reutilização de metadados.
- A referência indexada https://www.ceskatelevize.cz/api/docs não pôde ser aberta na consulta atual (resposta 410): não tratar documentação técnica antiga como autorização válida de uso de API ou de redistribuição.
- **Conclusão jurídica documental:** não localizada licença aberta inequívoca de republicação dos metadados do iVysílání. Verificar condições e eventuais direitos sobre base de dados ou obter autorização específica. HOLD mantido.

## Critérios ainda não cumpridos
- [ ] Documentar base legal/termos/licença que permitam republicação de metadados no MAR.
- [ ] Amostra estratificada e reproduzível de fichas por período, formato e estado de acesso.
- [ ] Verificação atual e reprodutível de disponibilidade HTTP de uma seleção suficiente (não realizada pela auditoria offline).
- [ ] Registro explícito do recorte, completude, limitações e fonte responsável.
- [ ] Revisão independente da projeção normalizada e das URLs de origem.
- [ ] Assinatura científica, responsável, data e versão da autorização.
- [ ] Gate automatizado validando a autorização antes da criação de índice público, seguido de Preview.

## Decisão
**HOLD.** Este documento registra pré-condições e evidências, mas não emite autorização. Nunca interpretar CI verde como aprovação de publicação. Não modificar `site/data/kavi-public.json`, base científica congelada, Streamlit ou main no âmbito deste dossiê.

## Campos para eventual autorização posterior
- Responsável pela revisão: **não atribuído**
- Data da aprovação: **não emitida**
- Identificador de ato/manifesto de aprovação: **inexistente**
- Política de licenças de metadados: **pendente**
- Faixa de registros autorizados: **nenhuma**
