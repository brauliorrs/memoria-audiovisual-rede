# MAR — F01: evidências de saída e autorrevisão do responsável

**Estado:** auditoria manual declarada concluída; aceite formal de encerramento F01 ainda não registrado. **Revisor humano disponível:** somente o proprietário `brauliorrs`, segundo declaração do próprio responsável em 19/11/2026. **Independência:** NÃO; não há segunda pessoa revisora. **F02:** não iniciada.

## Objeto aceito somente quando houver decisão explícita

F01 avalia a **completude e veracidade do inventário de migração**, nunca a paridade já entregue ou a validade científica/publicação de novos corpora. Fonte antiga de comparação: `app/streamlit_app.py`. O Streamlit não é parte desejada do produto final, mas continua preservado como referência técnica e possível rollback até F12.

- [Inventário dos 24 fluxos](mar-f01-functional-equivalence-inventory.json): 20 interfaces do Streamlit e quatro operações Python; 64 funções top-level e 13 declarações `st.tabs` mapeadas.
- Classificações verificadas estruturalmente: seis snapshots de interface disponíveis, doze parciais e seis operações sem equivalente. **Isso não é confirmação de equivalência de comportamento.**
- Testes: `scripts/check_mar_f01_equivalence_inventory.py`; `scripts/check_mar_f01_source_snapshot_parity.py`; suítes adversariais respectivas. Proteções de fonte/visibilidade de metadados no recorte KAVI 200, índice histórico e casos negativos.
- [PR #127, integrado na main](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/127): merge `1ff9758c835c703205f38e79c5d3cdc75c6f3af1`, por `brauliorrs`. **Não** houve review `APPROVED` de pessoa diferente do autor.
- [CI do PR](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/44569873276) no SHA `8d9363842befe7caaaad62c1f3963f07b5ad34d9`: SUCCESS.
- [CI da main após merge](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/44572638589) no SHA `1ff9758c835c703205f38e79c5d3cdc75c6f3af1`: SUCCESS.

## Matriz de impacto e prova negativa

| Superfície | Impacto observado no PR #127 | Critério de não divulgação |
|---|---|---|
| Manifesto da fila, script, testes de CI | Alterados para auditoria F01 e gate serial | Nenhum gate de F02 acionado; não emitir aceite científico a partir do CI |
| Documentação / matriz de migração | Criada/atualizada para auditar o legado | Não marcar como migradas páginas presentes sem comportamento equivalente |
| Streamlit, `src/`, `data/`, `site/` | **Nenhum desses caminhos estava na lista de arquivos alterados do PR #127** | Aplicação legada, motores, corpora e site preservados |
| Neon principal, SSO Vercel, mídias | Nenhuma alteração de configuração ou produção foi solicitada pela F01 | Nenhum banco/sistema remoto foi modificado por essa auditoria; ainda requer homologação própria das etapas futuras |

## Plano de reversão — apenas documentação e controles F01

**Não executar diretamente em produção.** Caso o PR #127 cause regressão real, criar branch temporária da main no SHA correspondente e testar `git revert -m 1 1ff9758c835c703205f38e79c5d3cdc75c6f3af1`, seguido de Quality Checks, diff limitado e revisão do responsável. Somente se o resultado for aceito, abrir PR de reversão. Não reverter nem manipular Neon, corpora ou deploy protegido como efeito colateral. Se houver PR de encerramento F01 posteriormente, reverter essa transição de manifesto separadamente para voltar a F01 ativa/F02 bloqueada.

**Estado do teste de rollback:** plano escrito; ensaio isolado de `git revert` **não executado** no registro deste documento. Não declarar o gate `rollback` aceito enquanto faltar ensaio ou justificativa de proporcionalidade analisada pelo responsável.

## Parecer humano do responsável único — pendência explícita

O responsável declarou: **“auditoria manual concluída”** e **“Só tem um revisor que sou eu”**. Essas declarações comprovam, como comunicação do responsável, a conclusão da atividade e a ausência de outro revisor. **Não constituem, por si só, parecer formal sobre todos os critérios abaixo**, pois não especificam SHA, riscos, divergências ou decisão `accepted`.

Antes de registrar `F01: completed`, o proprietário deve assinar na issue #128 uma decisão identificável com `F01`, escopo (auditoria, não paridade final), SHA do pacote, resultado **ACCEPTED** ou **REQUEST CHANGES**, riscos residuais e exceção `owner_only/independent=false`. A CI não comprova a autoria desse ato. Os gates `review`, `functional_acceptance` e `migration_matrix` só podem receber `result: accepted` após essa decisão; `impact` e `rollback` exigem seus próprios comprovantes.

**Sem liberação pública, sem inclusão de corpora e sem equivalência integral presumida.**