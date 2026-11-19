# MAR — F01: evidências de saída e autorrevisão do responsável

**Estado:** auditoria manual concluída e **aceite F01 ACCEPTED registrado pelo responsável único** na [issue #128, comentário 7016739721](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128#issuecomment-7016739721). Este documento é a evidência de auditoria para o PR de encerramento F01 → F02, não aprovação da migração integral. **Revisor humano disponível:** somente o proprietário `brauliorrs`, segundo declaração do próprio responsável em 19/11/2026. **Independência:** NÃO; não há segunda pessoa revisora. **F02:** não iniciada.

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

**Estado do teste de rollback:** ensaio isolado de **restauração de árvore Git** realizado no commit [fc27ad6b8a64180d4fc1619f5b9f86d368acabac](https://github.com/brauliorrs/memoria-audiovisual-rede/commit/fc27ad6b8a64180d4fc1619f5b9f86d368acabac) da branch `audit/mar-f01-isolated-rollback-tree-20261119`, filha do merge #127 (`1ff9758c835c703205f38e79c5d3cdc75c6f3af1`). A árvore resultante tem SHA `3fec31a81e10a519c8bc60c1184901ff49e81717`, **idêntico** à árvore da `main` anterior ao PR #127 (`66e79afa8755ca2ff12f1a8088c9ffc808a8a8a3`), com zero diferenças de arquivo na comparação. A `main` atual não foi alterada pelo ensaio. **Limites:** não executou literalmente `git revert -m 1`; não ensaiou conflitos com alterações subsequentes do PR #133, nem banco de dados, Vercel ou operações em produção. O plano de reversão do último merge requer um PR supervisionado, sem força/destruição de histórico. Para o escopo documental F01, essa prova de reversibilidade de árvore foi considerada proporcional e consta do aceite do responsável [na issue #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128#issuecomment-7016739721).

## Parecer humano do responsável único — aceite registrado

O responsável declarou: **“auditoria manual concluída”** e **“Só tem um revisor que sou eu”**. Essas declarações comprovam, como comunicação do responsável, a conclusão da atividade e a ausência de outro revisor. A decisão posterior do responsável foi **“sim”** à pergunta de aprovação formal da auditoria e de suas lacunas, sem afirmar migração concluída. Essa aprovação, vinculada à versão, ao escopo e aos riscos, consta do [termo de aceite na issue #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128#issuecomment-7016739721), assinado na conta `brauliorrs`.

O aceite **ACCEPTED** de F01 está registrado para a `main` de SHA `0b65f32366532bb24b8a9966f366c0ac85a2e8f7`, expressamente sob `owner_only`, `independent: false`. Os gates `review`, `functional_acceptance` e `migration_matrix` apontam para a decisão específica; `impact` e `rollback` têm evidências rastreáveis no histórico Git. A declaração e a documentação **não são independentes** e não substituem revisão científica, direitos de mídia ou homologação de F02–F13. O encerramento formal só passa a valer após CI e merge do PR que movimenta o manifesto.

**Sem liberação pública, sem inclusão de corpora e sem equivalência integral presumida.**