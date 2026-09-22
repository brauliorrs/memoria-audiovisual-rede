# Changelog

Este arquivo registra mudanças relevantes do **software** Memória Audiovisual em Rede.

O projeto adota Semantic Versioning para o software. Snapshots científicos de dados,
versões de schema e protocolos de validação possuem identificadores próprios e não
devem ser inferidos a partir da versão do pacote Python.

## [Unreleased]

## [0.1.0] - 2026-09-22

Primeira baseline formal do software. Esta versão estabelece um ponto de referência
reprodutível para o código existente sem reescrever retroativamente o histórico do
projeto.

### Added

- governança formal de releases;
- política de versionamento separando software, dados e schemas;
- checklist de release com gates verificáveis.

### Notes

- o metadata do pacote declara `0.1.0`;
- esta versão só deve ser tratada como release formal quando a tag `v0.1.0`
  apontar para o commit aprovado e existir uma GitHub Release correspondente;
- o histórico anterior não foi retroativamente reclassificado em versões sem
  evidência suficiente;
- a versão do software não substitui os identificadores próprios de snapshots
  científicos, schemas ou protocolos de validação e não reabre freezes científicos.
