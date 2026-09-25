# VAL-009 — ponte de captura na origem, sem execução independente

**Situação:** engenharia experimental; nenhuma coleta dos seis alvos da
minuta VAL-009 foi realizada. Entrega vinculada à issue #23, sobre a
`main` posterior ao PR #22; a tag imutável `v0.1.0` permanece intacta.

## Reconciliação dirigida com o v23 antigo

O branch científico `development/val-009-freeze-executor` contém
`ai_surface_discovery.py`, de grande escopo, com eventos
`SurfaceCapture` gerados no momento da requisição HTTP e separados dos
`SurfacePage` reduzidos para classificação. Não se incorporou esse
arquivo, seus dados ou o branch em bloco. A nova ponte
`val009_origin_bridge.py` oferece:

1. `capture_origin_http`: uma função de captura para uma **única URL
   já programada**, que recebe decisão/evidência de robots, cliente HTTP
   injetado, regra de escopo previamente definida e relógio explícito.
   Não faz descoberta nem classifica; nenhum site precisa ser visitado
   para testar o contrato.
2. `from_v23_origin_report`: tradução estrita da tupla
   `report.captures` gerada pelo coletor antigo, exigindo alinhamento
   com `report.pages` e verificação do hash do corpo. Um relatório
   derivado, sem os eventos originais, é recusado. A URL solicitada não
   é inferida de `SurfacePage.url`.
3. Extensão de `CapturedPage`, `Receipt` e manifesto de evidências:
   estados originais, bytes efetivamente recebidos, indicador de
   truncamento, evidência de robots, erro, página pai, profundidade e
   versão informada do coletor seguem até o armazenamento com SHA-256.

A URL final da origem conserva seus parâmetros **na ordem original**.
A `SurfacePage.url` do legado pode ordenar esses parâmetros; isso
não altera a evidência da requisição original. Quando a resposta não
existe, `final_url=None`: a URL solicitada permanece explícita, mas
não é apresentada como resultado de um redirecionamento inexistente.

## Semântica de estado e comprimento

`fetched` identifica resposta HTTP de classe 2xx/3xx em tipo de
conteúdo admitido. Uma resposta HTTP vazia (por exemplo, 204) gera
`empty_response_envelope`, que **não** se confunde com ausência de
resposta. `http_error` exige um status >=400 e também preserva corpo
vazio com esse envelope. `unsupported_content_type` identifica
resposta 2xx/3xx em formato não aceito, sem converter um HTTP bem
sucedido em falha HTTP. O redirecionamento para fora do escopo recebe
`redirect_outside_scope`, com URL externa conservada.

`blocked_by_robots` ocorre antes do GET da página: o evento conserva
prova da decisão, sem URL final nem código de resposta da página.
`request_error` inclui o tipo e a mensagem da exceção antes da
existência de resposta. Interrupção durante leitura do corpo é
bloqueante: nunca produz observação incompleta como se fosse sucesso.

A via HTTP lê até **limite + 1 byte** e conserva somente o prefixo do
limite predefinido. Se o byte extra aparecer, define
`response_truncated=true`, e
`response_received_bytes` indica apenas os bytes **efetivamente
observados**, não o comprimento total presumido do servidor.
Na tradução legada, `response_received_bytes` preserva o número
realmente registrado pelo antigo `SurfaceCapture`; um valor ausente
não é preenchido por suposição. O SHA-256 registra o prefixo efetivamente
capturado, não o conteúdo remoto integral quando truncado.

## Materialização e verificação

Os eventos passam por `build_capture_bundle` do PR #22. Todos são
persistidos antes da escolha da amostra e auditados em ordem; inclusive
URLs excluídas, duplicatas, respostas bloqueadas, erros e excesso de
limites. Os recibos contêm os metadados de origem; o manifesto de
evidências contém tanto a amostra quanto a auditoria completa.

`verify_capture_bundle` relê os recibos e bytes de **todas** as
observações do bundle, inclusive as não selecionadas. O
`guarded_capture_development_evaluate` só alcança qualquer calculador
após essa etapa e após `val009_preflight`. Testes com respostas
sintéticas verificam zero chamadas ao avaliador quando se alteram bytes
de evidência excluída.

O `evidence_manifest`, se futuramente pinado por uma testemunha
independente, inclui referências e hashes das evidências excluídas.
Isso **não** equivale a retenção externa desses bytes: cofre,
testemunha, imutabilidade e controle de acesso reais seguem pendentes.

## Limites preservados

- Esta ponte não incorpora o crawler v23 de 968 linhas nem realiza a
  coleta limitada dos seis alvos da minuta. A política de seleção,
  robots e travessia precisa ser congelada e submetida aos gates
  antes de qualquer uso científico real.
- Estados de robots e de truncamento exigem os dados **na origem**;
  relatórios legados que já perderam esses campos não são aceitos.
- Os testes usam exclusivamente dados artificiais e sessões HTTP
  falsas. Os `TrustedSeal` dos testes são sintéticos e não
  autenticam um testemunho externo.
- VAL-007 não foi alterada; CAL-008 segue como calibração de
  desenvolvimento; VAL-009 continua não selada/não executada;
  M4 permanece bloqueado.

**Próximo gate:** auditar a exposição suplementar após as 117 unidades
conhecidas e aliases, concluir manual de anotação e o plano operacional
de segregação custodiante/revisor, cofre privado e testemunho externo.
O pré-registro precisa ser consolidado/selado somente depois dessas
verificações, sem ajustes guiados por novos resultados.
