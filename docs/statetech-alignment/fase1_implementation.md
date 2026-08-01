# Fase 1 — núcleo executável de dados e proveniência

## Escopo

Este incremento implementa o núcleo operacional da camada Estado–tecnologia. Ele não adapta coletores, não executa auditorias empíricas e não publica resultados.

## Componentes implementados

- identificadores determinísticos para entidades;
- identificadores imutáveis de versão derivados do conteúdo;
- modelos de entidade, evidência e proveniência;
- validação integral com JSON Schema Draft 2020-12;
- ledger append-only com uma linha JSONL por transação lógica;
- registro conjunto de entidade, evidências e proveniência;
- índices reconstruíveis de entidades, versões e evidências;
- integridade referencial executável;
- cadeia obrigatória de `previous_version_id`;
- bloqueio de versões duplicadas e referências órfãs;
- aliases explicitamente curados para resolução de entidades;
- sugestões conservadoras de possíveis duplicidades, sem fusão automática;
- auditoria reconstruível da cadeia histórica;
- relatório estruturado de violações por código e severidade;
- inspeção e recuperação controlada de cauda truncada, sempre com backup;
- testes unitários do núcleo.

## Organização

```text
src/memoria_audiovisual/statetech/
├── audit.py
├── contracts.py
├── evidence.py
├── ids.py
├── index.py
├── integrity.py
├── ledger.py
├── models.py
├── persistence.py
├── recovery.py
├── resolution.py
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

## Resolução de entidades

Aliases somente entram no ledger após associação explícita a uma entidade e identificação da fonte e do revisor. A normalização remove diferenças de caixa, acentuação e pontuação. Similaridade lexical gera apenas candidatos para revisão; nunca promove fusão automática.

## Auditoria e recuperação

A auditoria percorre o ledger desde o início e pode registrar, entre outros:

- `VER-001`: versão duplicada;
- `VER-002`: primeira versão com predecessor;
- `VER-003`: cadeia histórica quebrada;
- `EVD-001`: evidência sem identificador;
- `EVD-002`: evidência duplicada;
- `EVD-003`: referência de evidência órfã.

A recuperação automática só é permitida quando o defeito está restrito à última linha. Antes do corte, o arquivo original é preservado com extensão `.bak`. Falhas no meio do ledger permanecem bloqueadas para análise humana.

## Garantias

1. Versões anteriores não são sobrescritas.
2. Uma versão idêntica não pode ser gravada duas vezes.
3. A atualização de entidade existente deve apontar para sua versão imediatamente anterior.
4. Referências a entidades inexistentes são bloqueadas antes do commit.
5. Evidências novas podem ser criadas e referenciadas na mesma transação.
6. Índices são derivados do ledger e podem ser reconstruídos.
7. Aliases conflitantes são bloqueados.
8. Duplicidades potenciais exigem decisão curatorial.
9. Reparos preservam cópia do ledger anterior.
10. A camada de publicação continua fora deste núcleo.

## Limites atuais

- não há banco relacional;
- não há controle de concorrência entre processos;
- a atomicidade é lógica, baseada em uma linha JSONL, e não ACID;
- a resolução utiliza aliases curados e similaridade lexical, não modelos semânticos;
- não há fusão ou redirecionamento automático de entidades;
- não há integração com os coletores existentes.

## Próximo incremento da Fase 1

- bloqueio de escrita e controle de concorrência;
- registro de decisões de merge, split e redirecionamento entre entidades;
- exportação do relatório de integridade no schema já definido;
- compactação segura de índices derivados;
- preparação da interface para os adaptadores da Fase 2.
