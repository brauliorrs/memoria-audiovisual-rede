# VAL-009: inventário suplementar de exposição — minuta

Esta revisão é **documental e offline**. Nenhum novo site foi visitado, nenhum classificador foi executado e nenhum selo científico foi emitido. O histórico analisado foi fixado no commit `4544bbc40e076cd7a81800a3c93ebbfb8efae5b2`.

As quatro fontes humanas conhecidas contêm 17 + 33 + 36 + 31 = **117 URLs distintas**. A inspeção de 17 relatórios históricos de descoberta (122 observações de páginas) identificou **20 páginas adicionais anteriormente coletadas**, ausentes da lista baseada nas unidades humanas. Assim, a união mínima documentada é **137 URLs conservadoramente distintas**.

| Fonte histórica | Adicionais |
| --- | ---: |
| EUscreen | 2 |
| Filmarchiv Austria | 8 |
| BBC | 2 |
| BNT | 2 |
| Cinemateca Portuguesa | 2 |
| Cinémathèque française | 2 |
| Memoryscapes | 2 |
| **Total** | **20** |

O inventário JSON versionado contém os SHA-256 das quatro fontes originais e dos 17 relatórios, datas/índices/URLs das 20 páginas e **22 URLs presentes apenas em testes**, separadas com `human_review_required` e `auto_exclusion=false`. Uma URL de teste não demonstra acesso HTTP ou alias. Os relatórios derivados históricos não provam a URL originalmente solicitada, a URL de destino nem os bytes HTTP brutos: esses campos não são reconstruídos.

O script `scripts/audit_val009_exposure.py` verifica, antes de gerar uma prévia não selada, que o checkout histórico é o SHA fixado, todos os arquivos possuem os hashes esperados e seus dados contêm exatamente a união documentada. O workflow `quality` executa o auditor contra um worktree independente no commit histórico. Os testes sintéticos de regressão **não substituem** essa auditoria integral.

O protocolo M3 2.3.0 ainda cita 117 exclusões. A futura revisão precisa considerar as **137 URLs documentalmente comprovadas**, sujeitas à revisão humana das 22 URLs de testes e de aliases adicionais efetivamente demonstrados. A presença anterior de código de integração Arkaader exige decisão metodológica específica sobre a independência da entidade estoniana proposta. Sem prova, não equiparar hosts, variantes linguísticas ou tecnologias.

Ainda são exigidos manual final, custodiante e revisor distintos, cofre restrito, testemunho externo e retenção independente dos snapshots. Nenhuma alteração da VAL-007, dos freezes, da tag `v0.1.0` ou promoção de M4 decorre deste inventário.

**Estado:** `draft_not_frozen`. O auditor jamais concede autorização de coleta independente ou certifica desempenho.
