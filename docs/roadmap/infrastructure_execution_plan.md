# Eixo executivo — infraestrutura científica, execução e expansão

## Regra central

O desenvolvimento segue esta ordem e não abre novas frentes antes da conclusão verificável da etapa anterior.

1. Criar, em português, a seção pública **Infraestrutura científica**.
2. Conectar catálogo de indicadores, metodologia e situação operacional.
3. Criar carregadores de resultados, manifests, histórico e snapshots.
4. Finalizar a validação controlada.
5. Executar a atualização integral dos corpora atuais.
6. Somente então construir e ativar o orquestrador da fila europeia.

## Bloqueio de internacionalização

Os catálogos `en.json` e `es.json` permanecem bloqueados até que:

- a infraestrutura portuguesa esteja integralmente exposta;
- os resultados e estados operacionais estejam conectados à interface;
- a validação controlada esteja concluída;
- os corpora atuais tenham sido atualizados pela nova infraestrutura.

## Situação dos componentes antecipados

Os componentes já criados para elegibilidade, sondagem técnica e fila europeia permanecem no repositório como infraestrutura preparatória, mas ficam **congelados para evolução funcional** até a conclusão das etapas 1 a 5.

Eles não podem:

- promover candidatos para `CORPORA`;
- alterar `organism_active`;
- automatizar decisão curatorial;
- iniciar expansão continental;
- publicar candidatos como corpus científico.

## Critérios de conclusão por etapa

### 1. Infraestrutura científica na interface

Concluída somente quando a interface portuguesa apresentar:

- catálogo oficial dos indicadores;
- fórmulas e regras metodológicas;
- cobertura e qualidade dos dados;
- proveniência, evidências e decisões curatoriais;
- snapshots, versões, hashes e integridade;
- estados operacionais sem confundir estrutura com resultado empírico.

### 2. Catálogo, metodologia e situação operacional

Concluída quando cada indicador informar:

- definição e pergunta científica;
- fórmula e componentes;
- fontes e critérios de inclusão/exclusão;
- política de dados ausentes;
- versão metodológica;
- estado: implementado, em validação, materializado, dados insuficientes ou não executado.

### 3. Carregadores de resultados e snapshots

Concluída quando a interface carregar, validar e tratar ausência de:

- `snapshot_indicators.json`;
- `manifest.json`;
- `indicator_history.jsonl`;
- relatórios de sensibilidade;
- matrizes de cobertura;
- metadados e hashes de integridade.

### 4. Validação controlada

Concluída somente com execução real, arquivos persistidos, nove indicadores processados, manifesto válido, sensibilidade produzida e inspeção dos resultados.

### 5. Atualização integral dos corpora atuais

Concluída quando todos os corpora ativos tiverem sido processados pela nova cadeia, com falhas, ausências e casos não avaliáveis registrados de modo explícito.

### 6. Orquestrador da fila europeia

Só pode ser iniciado após aprovação das etapas anteriores. Deve manter separadas:

- ingestão técnica;
- elegibilidade científica;
- decisão curatorial;
- incorporação em `CORPORA`.

## Próxima ação autorizada

Implementar a seção portuguesa **Infraestrutura científica** e seus carregadores, sem avançar na automação da fila europeia e sem iniciar os catálogos inglês e espanhol.
