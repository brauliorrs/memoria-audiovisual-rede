# Croatian Cinematheque / HDA — probe e decisão de HOLD

**Unidade da fila:** `fiaf-croatian-cinematheque`  
**Instituição:** Hrvatski Državni Arhiv — Hrvatska kinoteka  
**Rodada técnica:** Quality Checks #1825, run `37039961675`  
**Artifact:** `croatian-cinematheque-probe` id `11241806226`  
**Digest:** `sha256:a6cace83749b847c893a6364ae0e8a5baf30414179ced9d20d0e7f67bd42a68f`

## Resultado

O probe técnico passou integralmente no CI, mas o gate de incorporação ficou em:

`hold_robots_not_allowed_or_unverifiable`

O portal institucional `https://www.arhiv.hr/` respondeu normalmente e o `robots.txt`
do host retornou 404, tratado pelo contrato como ausente. As páginas institucionais da
Hrvatska kinoteka e do acervo fílmico foram acessíveis e confirmaram a superfície pública
institucional.

A pesquisa arquivística relevante, porém, está em `https://hais.arhiv.hr/`. No mesmo
executor do GitHub Actions, a tentativa de obter `https://hais.arhiv.hr/robots.txt`
terminou em `ConnectTimeout`. Por política fail-closed, o probe não acessou a busca HAIS,
não submeteu formulários e não tentou enumerar registros.

## O que foi demonstrado

- existência institucional da Hrvatska kinoteka e de acervo fílmico;
- portal HDA público e acessível;
- superfície HAIS identificada como próxima rota técnica a testar;
- nenhuma varredura de IDs;
- nenhum download de mídia;
- nenhum uso de M3/M4 ou classificador experimental;
- os aproximadamente 15.000 títulos sob custódia permanecem apenas como contexto custodial,
  nunca como denominador de completude web.

## O que não foi demonstrado

- política robots verificável no HAIS;
- paginação estável;
- isolamento reproduzível de registros audiovisuais;
- enumeração completa ou limitada do catálogo;
- disponibilidade pública de streaming.

## Decisão

A unidade é protocolada como **não incorporada nesta rodada**. O HOLD não bloqueia a
expansão da fila.

Um reteste futuro deve começar novamente por `hais.arhiv.hr/robots.txt` no mesmo executor.
Somente se a política for verificável e permitir a rota de pesquisa poderá ser executado
um probe limitado de formulários, paginação e identificadores estáveis.

Após este protocolo, a cabeça operacional da fila passa para
`fiaf-ifi-irish-film-archive` — **IFI Irish Film Archive**, mantendo rank compactado 6.
