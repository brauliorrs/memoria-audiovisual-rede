# Fase 1 — núcleo executável de dados e proveniência

## Escopo

Este incremento implementa o núcleo operacional da camada Estado–tecnologia. Ele não adapta coletores, não executa auditorias e não publica resultados.

## Componentes implementados

- identificadores determinísticos para entidades;
- identificadores imutáveis de versão derivados do conteúdo;
- modelos de entidade, evidência e proveniência;
- validação integral com JSON Schema Draft 2020-12;
- ledger append-only com uma linha JSONL por transação lógica;
- registro conjunto de entidade, evidências e proveniência;
- índices reconstruíveis de entidades, versões e evidências;
- integridade referencial executável;
- bloqueio de versões duplicadas;
- cadeia obrigatória de `previous_version_id`;
- bloqueio de referências órfãs;
- testes unitários do núcleo.

## Organização

```text
src/memoria_audiovisual/statetech/
├── __init__.py
├── contracts.py
├── evidence.py
├── ids.py
├── indexes.py
├── integrity.py
├── ledger.py
├── models.py
├── persistence.py
├── service.py
└── validation.py
```

## Fluxo de gravação

```text
entrada
→ validação do contrato
→ geração do entity_id e version_id
→ reconstrução do índice do ledger
→ validação da cadeia de versões
→ validação das evidências e referências
→ composição da proveniência
→ commit lógico único no ledger
```

## Garantias

1. Versões anteriores não são sobrescritas.
2. Uma versão idêntica não pode ser gravada duas vezes.
3. A atualização de entidade existente deve apontar para sua versão imediatamente anterior.
4. Referências a entidades inexistentes são bloqueadas antes do commit.
5. Evidências novas podem ser criadas e referenciadas na mesma transação.
6. Índices são derivados do ledger e podem ser reconstruídos.
7. A camada de publicação continua fora deste núcleo.

## Limites atuais

- não há banco relacional;
- não há controle de concorrência entre processos;
- a atomicidade é lógica, baseada em uma linha JSONL, e não ACID;
- a resolução semântica de entidades ainda é limitada aos identificadores determinísticos;
- não há recuperação automática de uma última linha fisicamente truncada;
- não há integração com os coletores existentes.

## Próximo incremento da Fase 1

- resolução de entidades e aliases;
- detecção de possíveis duplicidades por chaves alternativas;
- relatório estruturado de violações de integridade;
- verificação formal de toda a cadeia histórica de versões;
- recuperação controlada de cauda truncada do ledger;
- controle de concorrência e bloqueio de escrita.
