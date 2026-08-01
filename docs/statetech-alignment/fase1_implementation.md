# Fase 1 — núcleo executável de dados e proveniência

## Escopo deste incremento

Este incremento inicia a implementação operacional da arquitetura aprovada para a camada Estado–tecnologia. Não adapta coletores, não executa auditorias e não publica resultados.

## Componentes implementados

- identificadores determinísticos para entidades;
- identificadores imutáveis de versão derivados do conteúdo;
- modelos de entidade e proveniência;
- persistência local append-only em JSON Lines;
- leitura do registro central de schemas;
- validação estrutural mínima de campos obrigatórios, campos adicionais, enums e comprimento mínimo;
- serviço para registrar conjuntamente entidade, versão e proveniência;
- testes unitários do núcleo.

## Organização

```text
src/memoria_audiovisual/statetech/
├── __init__.py
├── contracts.py
├── ids.py
├── models.py
├── persistence.py
└── service.py
```

## Decisões

1. O módulo permanece dentro do pacote existente `memoria_audiovisual`.
2. A persistência inicial usa JSONL por ser simples, auditável e append-only.
3. Nenhuma versão anterior é sobrescrita.
4. A validação atual cobre apenas o subconjunto estrutural crítico do JSON Schema.
5. A validação integral Draft 2020-12, a integridade entre coleções e transações atômicas ficam para incrementos posteriores da Fase 1.

## Limites atuais

- não há banco relacional;
- não há índice persistente;
- não há controle de concorrência;
- não há validação completa de tipos, formatos ou referências estrangeiras;
- não há armazenamento de artefatos binários;
- não há integração com os coletores existentes.

## Próximo incremento da Fase 1

- registro executável de evidências;
- validação integral dos contratos;
- integridade referencial;
- índice de versões por entidade;
- unidade de gravação atômica entre entidade, evidência e proveniência;
- política de erros e recuperação.
