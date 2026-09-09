# Protocolo de evidência e validação

## Função deste protocolo

Este documento define como sinais coletados se tornam evidências revisadas e, quando permitido, afirmações publicáveis. Ele não substitui metodologias específicas de indicadores nem autoriza tratar uma detecção como fato institucional.

## Hierarquia de fontes

1. contrato, edital, adjudicação ou documento oficial;
2. relatório institucional, política ou documentação técnica oficial;
3. página oficial da instituição ou do fornecedor com relação explícita;
4. endpoint, metadado técnico, cabeçalho ou código público observado;
5. fonte secundária confiável;
6. inferência heurística, sempre marcada e não publicável sem confirmação adicional quando a alegação for sensível.

A posição na hierarquia não determina sozinha a qualidade: autenticidade, atualidade, escopo e relação direta com a alegação também devem ser avaliados.

## Tipos de evidência

`official_contract`, `procurement_notice`, `official_report`, `technical_documentation`, `institutional_webpage`, `provider_webpage`, `public_endpoint`, `html_or_header_signal`, `secondary_source`, `heuristic_inference`.

## Dimensões separadas

A infraestrutura distingue:

- **detecção:** resultado do procedimento automático ou manual de observação;
- **evidência:** fonte, trecho, artefato ou sinal vinculado ao objeto;
- **confiança:** avaliação da força e da relação da evidência;
- **decisão de revisão:** conclusão curatorial sobre a classificação;
- **elegibilidade de publicação:** decisão dependente da finalidade, cobertura e sensibilidade;
- **fato institucional:** formulação que somente pode ser usada quando a evidência e o processo de revisão sustentarem esse nível de certeza.

## Confiança da evidência

- `high`: relação explicitamente documentada por fonte primária adequada e atual;
- `medium`: evidências convergentes ou documentação técnica clara, com alguma limitação;
- `low`: sinal isolado, indireto, parcial ou sujeito a interpretação;
- `unknown`: evidência insuficiente para graduar.

Confiança alta não elimina a necessidade de revisão nem transforma automaticamente uma observação em indicador.

## Estados de revisão

- `pending_review`: detecção ou registro ainda não revisado;
- `confirmed`: classificação sustentada para a finalidade declarada;
- `probable`: evidência forte, mas incompleta para confirmação plena;
- `inconclusive`: evidência não permite decisão segura;
- `false_positive`: detecção rejeitada;
- `not_assessable`: rota, fonte, formato ou cobertura impedem classificação válida;
- `needs_more_evidence`: revisão requer fontes adicionais;
- `withdrawn_or_corrected`: decisão anterior retirada ou corrigida, preservando o histórico.

## Estados negativos e ausência

- `not_identified` significa que nenhuma evidência compatível foi encontrada nas superfícies e pelo procedimento declarados;
- `not_assessable` significa que uma classificação válida não foi possível;
- `error` significa que a observação falhou tecnicamente;
- nenhum desses estados comprova inexistência institucional.

## Regras de publicação

- a metodologia de cada produto define quais estados podem entrar no numerador, denominador ou descrição pública;
- `confirmed` e `probable` devem permanecer separados quando ambos forem publicados;
- `pending_review`, `inconclusive`, `not_assessable`, `needs_more_evidence` e `error` não entram como ausência confirmada;
- `false_positive` e correções permanecem no histórico metodológico, mas não alimentam resultados positivos vigentes;
- contratos, fornecedores, fluxos de dados e IA não podem ser afirmados apenas por associação de domínio, tecnologia ou marca;
- trechos de evidência devem ser proporcionais, curtos e compatíveis com direitos autorais e proteção de dados;
- toda revisão registra data, responsável, decisão, evidências e nota curatorial;
- alegações sensíveis podem exigir dupla revisão, quorum ou supressão pública.

## Critérios mínimos por objeto

### Fornecedor

Nome identificável, papel tecnológico e evidência da relação com a instituição. Detecção de software não prova quem fornece, mantém ou contrata o sistema.

### Contrato

Autoridade contratante, objeto ou fornecedor e identificador ou documento público. A ausência de contrato localizado não prova inexistência de vínculo.

### Fluxo de dados

Origem, destino, tipo de fluxo, finalidade e evidência técnica ou documental. Serviços incorporados ou scripts de terceiros não bastam para afirmar transferência institucional de dados.

### IA

Função concreta, objeto associado, estágio ou contexto de uso e evidência explícita. Aplicam-se também os estados e cautelas de [`ai_systems_protocol.md`](ai_systems_protocol.md).

### Risco

Regra versionada, evidências subjacentes, linguagem proporcional e revisão humana. Risco é uma avaliação analítica, não um fato diretamente detectado.

## Princípio de não inferência

Ausência de detecção significa somente **não identificado na superfície, no período e pelo procedimento observados**. Toda comunicação pública deve preservar esse limite.
