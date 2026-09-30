# Relação entre o corpus pré-existente do MAR e o desenvolvimento do M3

**Auditoria documental concluída em 30/09/2026.**  
**Escopo:** evidências versionadas no repositório.  
**Resultado:** as seis instituições propostas para a VAL-009 já integravam o corpus geral do MAR antes da criação do M3, mas **não foram usadas como unidades humanas rotuladas nos 117 casos que alimentaram a calibração e o desenvolvimento documentados do classificador**. Não foi identificada dependência direta do código M3 em relação aos arquivos gerais desses seis corpora. Influência humana informal, não registrada em artefatos versionados, não pode ser provada nem excluída retrospectivamente.

A trilha computável está em [`m3-corpus-relation-audit.json`](m3-corpus-relation-audit.json).

## 1. Questão auditada

A questão não é simplesmente se uma instituição “já estava no projeto”. Há quatro relações metodologicamente diferentes:

1. **presença no corpus geral do MAR**;
2. **uso como dado rotulado para calibrar ou corrigir o M3**;
3. **dependência direta do código do M3 em arquivos do corpus geral**;
4. **familiaridade humana anterior com o corpus, capaz de produzir influência indireta não documentada**.

A auditoria separa essas quatro dimensões.

## 2. Cronologia

Os seis corpora que haviam sido propostos para a VAL-009 foram materializados entre junho e julho de 2026:

| Entidade | Raiz registrada | Snapshot geral MAR |
| --- | --- | --- |
| Cinémathèque de Bretagne | `https://www.cinematheque-bretagne.bzh/voir-les-films-426-0-0-0.html` | 19/06/2026 |
| CINEMATEK | `https://cinematek.be/en/collections/be-film` | 06/07/2026 |
| DR/Gensyn | `https://www.dr.dk/drtv/gensyn` | 13/07/2026 |
| ERT | `https://archive.ert.gr/` | 14/07/2026 |
| Estonian Film Archive/Arkaader | `https://arkaader.ee/landing/br/rHczO7kKnl/pbOiQfMOLr` | 15/07/2026 |
| Filmoteca de Catalunya | `https://filmo.platfo.es/pages/home` | 17/07/2026 |

Esses arquivos já estavam versionados quando o M3 foi criado. O commit inicial do classificador de superfícies é de **19/08/2026** (`1e660820...`). Portanto, há **exposição cronológica do projeto**: os dados gerais existiam antes do instrumento.

Isso impede a afirmação “essas seis instituições nunca haviam sido vistas pelo MAR”. Não demonstra, porém, que tenham sido usadas para desenvolver o M3.

## 3. Fontes realmente usadas no desenvolvimento documentado do M3

A linhagem dos dados humanos do M3 é explícita e soma **117 unidades**:

| Etapa | Unidades | Instituições |
| --- | ---: | --- |
| calibração inicial | 17 | ARCHIPOP, BFI, ECPAD, Europeana, INA |
| VAL-003 → desenvolvimento 2.1 | 33 | Ciné-Archives, Cinémémoire, EAFA, Eye, Archivio Luce |
| VAL-005 → desenvolvimento 2.2 | 36 | CICLIC, CINÉAM, Czech Television, DFF, EUscreen |
| VAL-007 → desenvolvimento 2.3 | 31 | BBC, BNT, Cinemateca Portuguesa, Cinémathèque française, FINA, Memoryscapes |

**Interseção entre essas 117 unidades e as seis instituições propostas para VAL-009: zero instituições.**

Esse resultado é forte porque a documentação de cada etapa declara expressamente quando uma validação encerrada passou a ser reutilizada como dado de desenvolvimento. A evolução 2.0 → 2.1 → 2.2 → 2.3 segue essa trilha.

## 4. O que o código mostra

O primeiro `surface_typing.py` é um classificador determinístico que recebe campos da página — URL, raiz, título, texto, metadados estruturados, mídia e estado de coleta. O módulo não carrega `data/output`, não abre snapshots institucionais e não contém os nomes ou domínios das seis instituições.

Na versão inicial, os testes com domínios reais usam INA e ECPAD; os demais exemplos são sintéticos.

O candidato `2.3.0-dev` continua como camada determinística sobre o classificador congelado 2.2.0. Também não contém os nomes/domínios das seis instituições nem carrega seus exports gerais.

Isto sustenta a seguinte afirmação limitada:

> **não foi encontrada dependência direta, versionada e executável entre os seis corpora gerais e a lógica do M3 auditada.**

Isso não equivale a provar que nenhum pesquisador ou desenvolvedor havia visto as páginas anteriormente.

## 5. De onde vieram as mudanças do candidato 2.3

Aqui a evidência é especialmente clara.

A documentação de CAL-008 registra que o candidato 2.3 foi construído **depois da falha da VAL-007**, utilizando aquelas 31 decisões humanas como diagnóstico de desenvolvimento. Os próprios testes do candidato sintetizam estruturas observadas nessa validação:

- `Ficha.aspx?...&type=Video` e `Colecoes/Filme-e-Video.aspx` correspondem às estruturas da **Cinemateca Portuguesa**;
- `/henri/film/<filme>/` corresponde à **Cinémathèque française**;
- `/en/clips/<id>` e `/en/archive/?authors=...` correspondem a **Memoryscapes**.

Os domínios foram substituídos por `example.org` em testes sintéticos, mas a origem dos padrões está documentada na análise pós-VAL-007.

Portanto, há **relação causal de desenvolvimento explicitamente documentada** entre VAL-007 e o candidato 2.3. Não há relação equivalente documentada com CINEMATEK, Cinémathèque de Bretagne, DR, ERT, Arkaader ou Filmoteca de Catalunya.

## 6. O que permanece impossível de demonstrar retrospectivamente

Como os seis corpora estavam no projeto antes do M3, é plausível que o pesquisador/desenvolvedor tivesse familiaridade geral com algumas de suas estruturas. Git, testes e artefatos podem demonstrar entradas registradas no processo de desenvolvimento; eles **não conseguem provar a ausência de memória humana ou consulta informal não registrada**.

Assim, três afirmações seriam metodologicamente inadequadas:

- “não houve qualquer influência indireta”, porque não é verificável;
- “houve contaminação”, porque não existe evidência documental que sustente essa conclusão;
- “as instituições eram inéditas”, porque isto é objetivamente falso no nível do projeto MAR.

A formulação correta é:

> **as seis instituições eram previamente conhecidas no corpus geral MAR, mas permaneceram fora dos conjuntos humanos rotulados e documentados usados para calibrar o M3; não há evidência versionada de uso direto de seus exports no classificador. Influência informal residual não pode ser excluída retrospectivamente.**

## 7. Consequência para a VAL-009

Para a função que a VAL-009 deveria exercer — avaliar o classificador de superfícies — **novidade institucional absoluta em relação ao projeto MAR não é requisito lógico**, desde que a pergunta científica seja corretamente delimitada.

É defensável avaliar o M3 em:

> **novas unidades/superfícies, ainda não rotuladas para o M3, pertencentes a instituições ausentes dos conjuntos humanos usados no desenvolvimento do classificador.**

Essa validação testa capacidade de classificação em **dados rotulados novos para o M3**. Não testa a hipótese mais forte de generalização para instituições completamente desconhecidas do projeto.

Por rigor, a VAL-009 deverá:

1. declarar que as seis instituições já existiam no corpus geral MAR;
2. declarar que nenhuma delas integra os 117 casos humanos usados no desenvolvimento do M3;
3. excluir páginas/aliases já expostos aos experimentos M3 e demais URLs comprovadamente conhecidas;
4. congelar versão, protocolo e predições antes da revisão humana;
5. manter o revisor humano cego às previsões;
6. proibir qualquer ajuste do M3 após acesso aos rótulos VAL-009;
7. relatar a familiaridade prévia com o corpus como limitação de independência institucional global, e **não** como vazamento de rótulos comprovado.

## 8. Parecer metodológico

**Não há evidência de vazamento direto dos seis corpora gerais para os dados rotulados de desenvolvimento do M3.** A relação documentada é de coexistência anterior no projeto, não de utilização como conjunto de calibração.

Por isso, a opção metodologicamente mais coerente com o objetivo do MAR é **preservar as seis instituições para uma validação do instrumento**, desde que o protocolo abandone qualquer formulação de “instituições inéditas no MAR” e adote a formulação mais precisa: **instituições fora dos conjuntos humanos anteriores do M3, com unidades e rótulos novos para o experimento**.

Se o projeto desejar, adicionalmente, demonstrar generalização para instituições inteiramente desconhecidas do MAR, isso deve constituir **um estudo externo/prospectivo próprio**, e não uma exigência retroativa desta validação.

Este parecer não é uma assinatura independente do protocolo. O selo VAL-009 continua condicionado aos controles de exclusão, cegamento, custódia, anotação, retenção de evidências e revisão formal já documentados.
