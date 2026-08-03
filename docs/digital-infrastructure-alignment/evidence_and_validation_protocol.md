# Protocolo de evidência e validação

## Hierarquia de fontes

1. contrato, edital, adjudicação ou documento oficial;
2. relatório institucional, política ou documentação técnica oficial;
3. página oficial do fornecedor ou da instituição com relação explícita;
4. metadados técnicos, cabeçalhos, código público ou endpoint observado;
5. fonte secundária confiável;
6. inferência heurística, sempre marcada como tal.

## Tipos de evidência

`official_contract`, `procurement_notice`, `official_report`, `technical_documentation`, `institutional_webpage`, `provider_webpage`, `public_endpoint`, `html_or_header_signal`, `secondary_source`, `heuristic_inference`.

## Confiança

- `high`: relação explicitamente documentada por fonte oficial primária;
- `medium`: múltiplas evidências convergentes ou documentação técnica clara;
- `low`: sinal isolado, indireto ou sujeito a interpretação;
- `unknown`: evidência insuficiente para graduar.

## Estados de validação

- `pending_review`: ainda não revisado;
- `confirmed`: sustentado por evidência suficiente;
- `probable`: forte, mas sem confirmação documental completa;
- `inconclusive`: não permite afirmação segura;
- `false_positive`: detecção rejeitada;
- `not_assessable`: fonte inacessível ou objeto não avaliável.

## Regras de publicação

- indicadores públicos usam apenas `confirmed` e, quando explicitado, `probable`;
- resultados `probable` devem ser separados dos confirmados;
- `pending_review`, `inconclusive` e `not_assessable` não entram como ausência;
- `false_positive` permanece no histórico metodológico, mas não no resultado positivo;
- contratos, fornecedores e IA não podem ser afirmados apenas por associação de domínio;
- trechos de evidência devem ser curtos e respeitar direitos autorais;
- toda revisão deve registrar data e nota curatorial.

## Critérios mínimos por objeto

### Fornecedor
Nome identificável + papel tecnológico + evidência da relação com a instituição.

### Contrato
Autoridade contratante + fornecedor ou objeto + identificador/URL documental.

### Fluxo de dados
Origem + destino + tipo de fluxo + evidência técnica ou documental.

### IA
Função concreta + estágio ou contexto de uso + evidência explícita. Menções genéricas a inovação não contam.

### Risco
Regra de classificação documentada + evidências subjacentes + revisão humana.

## Princípio de não inferência

Ausência de detecção significa somente `não detectado na superfície e rodada observadas`; nunca significa inexistência institucional.