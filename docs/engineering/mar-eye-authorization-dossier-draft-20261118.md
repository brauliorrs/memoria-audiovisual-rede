# MAR — Dossiê de admissibilidade documental: Eye Filmmuseum

**Versão:** minuta técnica 2026-11-18  
**Decisão vigente:** HOLD — **NÃO É UMA AUTORIZAÇÃO**  
**Escopo:** somente metadados textuais e links de origem; nenhuma licença presumida para mídia, cópia, player ou captura.

## Evidência interna
- Fonte histórica: `data/output/eye_catalogo_videos_analitico.csv`.
- SHA-256 confirmado em CI: `222d16e0ac744c79ef21823b9e9cf22bb576faebe6a32ae87382bfc42f9fcf7a`.
- Linhas auditadas: **630**; URLs oficiais sintaticamente válidas e distintas: **630**.
- IDs derivados e distintos: **630**.
- Duplicatas exatas, equivalências de URL, colisões de ID, conflitos de título, divergências institucionais detectadas: **zero**.
- Auditoria offline: https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/44361604953
- Artefato auditável (retenção 30 dias): https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/44361604953/artifacts/14456100644

## Evidência externa
- Fichas documentais amostradas e localizadas: 7/7, em 18/11/2026.
- Evidências individuais: `docs/engineering/mar-multicorpus-expanded-sample-20261118.md`.
- A verificação externa foi intencional e não probabilística; não representa os 630 registros.
- A URL antes pendente `als-het-verleden-spreekt` foi recuperada pela navegação institucional.
- O ano de produção das obras não deve ser inferido a partir de campos vazios no CSV.

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
