# Instrumentos de análise admitidos na operação do MAR

**Política vigente:** somente instrumentos com escopo, validação e limites documentados podem ser chamados pelo executor de produção. Instrumentos experimentais permanecem no laboratório e não podem modificar ou sustentar produtos analíticos públicos.

Esta página documenta a eficácia **dentro do escopo declarado** dos instrumentos atualmente admitidos. Ela não transforma regras descritivas em modelos preditivos nem amplia seus limites de inferência.

## 1. Auditoria descritiva de acesso restrito

**Instrumento:** `restricted_access_audit`  
**Versão:** `2026-06-acesso-pago-restrito-v1`  
**Estado:** produção, escopo descritivo.

### Função

Materializar uma tabela auditável de modalidades de acesso explicitamente registradas no corpus e nas decisões de não incorporação, distinguindo:

- catálogo comercial de licenciamento;
- streaming pago/autenticado;
- mídia local ou autorizada;
- categorias de não incorporação documentadas;
- banco privado/comercial mantido fora do corpus ativo.

O instrumento **não descobre restrições desconhecidas** nem classifica a instituição inteira. Ele resume estados explícitos já presentes nos registros e em decisões metodológicas versionadas.

### Evidência de eficácia

A eficácia requerida é **conformidade determinística com as categorias declaradas**, não acurácia de um classificador estatístico. A suíte `tests/test_restricted_access_audit.py` verifica:

- separação entre banco privado e modalidades do corpus ativo;
- preservação de casos não incorporados com categoria própria;
- contagem correta de unidades e registros;
- materialização dos arquivos de saída;
- manutenção do estado de corpus e da decisão metodológica.

O instrumento foi admitido porque sua saída é uma transformação reprodutível de campos e categorias já curados. Erros nos dados de entrada continuam sendo limitações do resultado.

### Limites

A saída pode sustentar contagens e descrições **dos registros materializados**. Não sustenta prevalência institucional completa, dimensão total dos acervos, inferência causal ou ausência de restrição fora das superfícies observadas.

---

## 2. Indicador de registros públicos materializados

**Instrumento:** `public_access_index`  
**Versão:** `2026-06-indice-dados-publicos-v2`  
**Estado:** produção, indicador descritivo com denominador restrito.

### Função

Calcular, para o conjunto efetivamente materializado, a proporção de registros classificados pelas regras do corpus como:

- `publico_materializado`;
- `restrito_autorizacao_cadastro_pagamento`.

O denominador é explicitamente **o total de registros audiovisuais materializados**, e não o acervo físico, o universo institucional nem uma amostra probabilística da Europa.

### Evidência de eficácia

A suíte `tests/test_public_access_index.py` verifica:

- classificação de exemplos públicos e restritos;
- proteção contra falsos positivos lexicais conhecidos;
- separação de bancos privados fora do denominador;
- agregação por mundo, continente e corpus;
- materialização das três saídas versionadas.

O indicador é admitido como medida descritiva porque sua fórmula e denominador são explícitos, seus casos de borda possuem testes e o resultado não depende de um modelo experimental.

### Limites

O nome histórico do arquivo contém “índice”, mas este instrumento **não é o futuro índice composto de visibilidade audiovisual digital**. Não mede abertura institucional total, encontrabilidade, visibilidade algorítmica, cobertura dos acervos ou representatividade populacional.

---

## 3. Captura de evidências de infraestrutura digital

**Instrumento:** `digital_infrastructure_evidence`  
**Estado:** captura de evidência; **não** análise automática publicável.

O detector de CMS, APIs, metadados, interoperabilidade, busca, restrições e sinais textuais de IA é admitido somente como **coletor heurístico de evidências**. Seu protocolo de validação está em [`docs/infrastructure-audit/VALIDATION_PROTOCOL.md`](../infrastructure-audit/VALIDATION_PROTOCOL.md).

A saída bruta pode alimentar revisão curatorial. Uma detecção não revisada não autoriza, sozinha, uma afirmação institucional. O instrumento também não pode transformar ausência de sinal em ausência da tecnologia.

Por essa razão, ele não é executado automaticamente no ciclo global de produção. Pode ser executado em rodada própria, com snapshot, ledger e revisão.

---

## 4. Instrumentos ainda fora da produção

Os seguintes instrumentos permanecem isolados:

- **M3 2.3.0-dev:** candidato experimental; VAL-009 ainda em `DRAFT/HOLD`;
- **M4:** gate histórico reprovado, promoção bloqueada;
- **avaliação de relevância do motor de busca:** ainda sem conjunto de consultas e julgamentos humanos de relevância;
- **índice composto de visibilidade audiovisual digital:** objetivo de pesquisa ainda sem definição versionada e validação.

Nenhum desses instrumentos pode ser chamado pelo executor de produção.

## 5. Regra de promoção

Uma ferramenta só muda para `production` quando todos os itens abaixo forem versionados:

1. objetivo e unidade de análise;
2. implementação identificável por versão;
3. protocolo ou método de validação;
4. resultado de eficácia adequado ao tipo de instrumento;
5. casos de falha conhecidos;
6. limites de inferência;
7. testes automatizados do contrato;
8. documentação das saídas;
9. decisão explícita de admissão no registro;
10. CI verde na alteração que promove o instrumento.

A incorporação de novos corpora **não depende** da promoção de ferramentas experimentais. Essa separação permite que o observatório continue crescendo enquanto o laboratório metodológico desenvolve e valida novos instrumentos.
