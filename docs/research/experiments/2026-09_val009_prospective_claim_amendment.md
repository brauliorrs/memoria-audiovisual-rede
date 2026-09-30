# VAL-009 — emenda prospectiva da pergunta científica e do alcance

**Data:** 30/09/2026  
**Estado:** **minuta prospectiva**, sem selo, sem execução e sem assinatura de revisor independente.  
**Experimento:** `MAR-T2A-M3-VAL-009`.

Esta emenda formaliza a consequência metodológica da auditoria [corpus MAR → desenvolvimento M3](../../methodology/m3-corpus-relation-audit.md). Ela **não altera retroativamente** a VAL-007, não reescreve os dados históricos e não autoriza coleta ou geração de previsões.

## 1. Decisão metodológica proposta

As seis instituições originalmente selecionadas são **mantidas**:

1. CINEMATEK;
2. Cinémathèque de Bretagne;
3. DR / Gensyn;
4. ERT;
5. Estonian Film Archive / Arkaader;
6. Filmoteca de Catalunya.

A auditoria demonstrou que todas já integravam o corpus geral MAR antes da criação do M3, mas nenhuma delas aparece nas **117 unidades humanas rotuladas** que alimentaram a linhagem documentada de desenvolvimento do classificador.

A novidade relevante para esta validação é, portanto, **novidade para o processo humano de desenvolvimento do M3**, e não novidade absoluta para o projeto MAR.

## 2. Pergunta científica consolidada

> **O candidato M3 2.3.0 classifica adequadamente superfícies digitais públicas previamente não rotuladas, provenientes de seis instituições ausentes de todos os conjuntos humanos usados no desenvolvimento do M3, sob protocolo congelado de seleção, cegamento e avaliação?**

Essa pergunta delimita o objeto correto: a confiabilidade do **instrumento M3**.

## 3. O que um eventual resultado poderá sustentar

Se o protocolo for selado e executado sem desvios, o resultado poderá sustentar conclusões sobre o desempenho do candidato congelado:

- nas superfícies efetivamente selecionadas;
- nas seis instituições pré-especificadas;
- com os rótulos humanos produzidos após o freeze das previsões;
- sob a regra de coleta e seleção registrada;
- nos limites da composição e do tamanho da amostra.

Mesmo um eventual `PASS` **não** demonstrará:

- generalização para instituições inteiramente desconhecidas pelo MAR;
- representatividade de todos os arquivos audiovisuais europeus;
- prevalência das classes de superfície;
- completude dos acervos;
- validade de todos os instrumentos da plataforma;
- uso institucional de IA;
- presença de IA em conteúdo audiovisual;
- autorização automática para M4.

## 4. Por que preservar as seis entidades

A validação científica deve corresponder ao que o M3 precisa demonstrar. O classificador não tem como tarefa reconhecer instituições desconhecidas; ele deve classificar o **papel semântico de superfícies digitais** a partir de evidências observáveis.

Assim, o risco metodológico relevante é o modelo ter sido ajustado aos rótulos ou às páginas específicas que serão usadas para avaliá-lo. A auditoria documentou:

- zero sobreposição institucional entre as seis propostas e os 117 casos humanos de desenvolvimento M3;
- ausência de dependência direta do código M3 auditado em relação aos exports gerais dos seis corpora;
- origem explicitamente documentada das mudanças 2.3 nas famílias de erro de VAL-007;
- impossibilidade retrospectiva de provar ou excluir familiaridade humana informal com os corpora gerais.

A familiaridade geral anterior deve ser relatada como **limitação da alegação de novidade institucional global**, e não como vazamento de rótulos demonstrado.

## 5. O que permanece congelado da minuta original

Esta emenda **não modifica**:

- ordem das seis instituições e suas URLs de entrada;
- profundidade máxima, limites por entidade e tamanho máximo da amostra;
- mínimo de 24 unidades provenientes de pelo menos cinco entidades;
- seleção antes da classificação;
- ausência de substituição de entidades orientada por resultado;
- vocabulário das classes;
- métricas e limiares;
- separação entre tipagem e estado de acesso;
- sequência de freeze;
- cegamento do revisor;
- proibição de ajuste após acesso aos rótulos;
- bloqueio de M4 até decisão científica posterior.

O protocolo histórico permanece preservado no commit `4544bbc40e076cd7a81800a3c93ebbfb8efae5b2`. A emenda é um **overlay prospectivo**; ela somente poderá ser incorporada ao protocolo executável depois da revisão independente.

## 6. Estado das exclusões

A auditoria documental elevou o piso comprovado de URLs historicamente conhecidas de 117 para **137**:

- 117 unidades provenientes das quatro rodadas humanas conhecidas;
- 20 páginas adicionais previamente coletadas nos relatórios históricos.

Além disso:

- 22 strings encontradas em testes estão em revisão metodológica separada;
- sete fragmentos foram reconstruídos em oito expressões completas;
- nenhuma dessas 22 strings foi automaticamente transformada em visita HTTP comprovada;
- nenhum alias `requested_url → final_url` legado foi comprovado apenas por inferência.

Consequentemente, o manifesto final de exclusão **não poderá conter menos de 137 URLs comprovadas**. Pode crescer antes do selo, desde que toda inclusão tenha fonte, classe de evidência e decisão metodológica registrada.

## 7. Independência e cegamento

Para que a VAL-009 seja interpretável:

1. o candidato final deve ser congelado antes da coleta;
2. a coleta e a seleção devem ocorrer sem consultar predições;
3. as predições devem ser geradas e seladas antes da anotação humana;
4. o revisor não pode acessar as predições durante a revisão;
5. a revisão humana deve ser congelada antes da abertura das predições;
6. a avaliação deve ocorrer uma única vez, usando as regras pré-especificadas;
7. qualquer ajuste posterior do modelo cria uma nova versão e exige outra validação independente.

A infraestrutura já implementada para fail-closed, proveniência e captura é necessária, porém **não substitui esses controles operacionais**.

## 8. Situação acadêmica

A decisão de **reter as seis instituições e estreitar a alegação** é a proposta metodológica do projeto decorrente da auditoria. Ainda falta a concordância formal de um revisor do protocolo que não esteja atuando como custodiante das predições.

Até essa concordância:

- `VAL-009 = DRAFT / HOLD`;
- não existe selo;
- não existe amostra independente executada;
- não existem novas predições válidas;
- M4 permanece bloqueado.

O artefato computável desta emenda é
[`m3_surface_type_val009_amendment_v2_3_draft.json`](../../data/digital_infrastructure/ai_experiments/m3_surface_type_val009_amendment_v2_3_draft.json).

## 9. Gates remanescentes antes do selo

A ordem recomendada é:

1. finalizar a decisão das 22 strings e das oito expressões reconstituídas;
2. consolidar o manifesto final de exclusões e aliases;
3. congelar a implementação final `2.3.0`;
4. concluir o manual de anotação;
5. designar custodiante e revisor distintos;
6. definir armazenamento durável e restrito das predições;
7. definir retenção dos snapshots selecionados e não selecionados;
8. obter testemunho/selo externo autenticado;
9. executar o preflight fail-closed;
10. somente então autorizar a coleta VAL-009.

Nenhuma dessas pendências deve ser resolvida observando resultados novos do modelo.
