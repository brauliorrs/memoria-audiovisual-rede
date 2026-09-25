# VAL-009 — proveniência de coleta e snapshots brutos

**Estado:** entrega técnica em desenvolvimento. Não foi executada nenhuma coleta
independente, não há novo selo científico e a versão do software `v0.1.0` não
é alterada. Issue de origem: #21. Este adaptador é deliberadamente separado
dos coletores históricos e dos branches científicos divergentes.

## Problema específico resolvido

O coletor legado pode substituir a URL solicitada pela URL final; isso
eliminaria parte da proveniência do redirecionamento. O módulo
`val009_capture_provenance.py` exige que o chamador entregue ambas
explicitamente: `requested_url` e `final_url`. Quando uma tentativa falha
antes de conhecer a URL final, `final_url=None` permanece desconhecida:
`page_url` identifica somente a solicitação observada nesse caso e **não**
afirma que a URL final foi determinada.

`CapturedPage` contém entidade, raiz, as duas URLs, índice de descoberta
por entidade, timestamp com fuso, estado da captura, bytes brutos, eventual
código HTTP e mídia. O adaptador **não faz** requisições de rede ou
classificações. Ele recebe os registros do coletor, sem inventar campos
ausentes de relatórios anteriores.

## Persistência

`CaptureStore.persist` grava, sem reserialização, os bytes exatos das
respostas não vazias em arquivos content-addressed com SHA-256 e `fsync`,
mais um recibo imutável por observação. O recibo preserva as URLs e os
metadados necessários, inclusive para redirecionamentos. Um corpo HTTP de
erro, quando disponível, também é preservado byte a byte.

Se não existirem bytes de resposta (como em um timeout, bloqueio ou erro
HTTP de corpo vazio), grava-se um **envelope de ausência**, explicitamente
identificado. Seu campo `raw_body_sha256` é o hash dos bytes vazios; o
`snapshot_sha256` é o hash do próprio envelope, não um hash inventado de
uma página que nunca chegou. Uma resposta declarada `fetched` não pode
usar esse envelope.

`CaptureStore.load` confere novamente o corpo e o recibo armazenados,
detectando exclusão ou alteração dos bytes. É um mecanismo técnico local:
um diretório não prova retenção WORM, custódia separada, timestamp confiável,
controle de acesso ou confiabilidade de sua origem. Nenhuma previsão é
gravada por este módulo.

## Ordem de coleta, exclusões e seleção

`build_capture_bundle` valida os índices `0..N-1` de cada entidade e
segue a ordem das entidades fixada no protocolo. Todos os registros,
inclusive erros, duplicatas, exclusões e excesso de limite, são
persistidos **antes** de produzir os manifestos. Cada registro auditado
recebe `global_discovery_order`, ID determinístico, URL solicitada e
final, referência e SHA-256 de snapshot, hash do corpo, estado e timestamp.

A identidade de URL normaliza esquema/host/porta padrão e remove
fragmento, **sem** alterar caixa do caminho nem os valores/ordem da query.
Exclusões e deduplicação consultam tanto a URL solicitada quanto a final.
Mantém-se a primeira ocorrência; todas as outras ficam registradas na
auditoria do manifesto de evidências com o motivo explícito
(`known_url`, `duplicate`, `entity_cap`, `global_cap`).

A seleção ocorre antes da classificação e gera:
- `selection`, com IDs, entidade, URLs, snapshot e ordem;
- `evidence_manifest`, com evidências selecionadas e auditoria de **todos**
  os registros observados;
- `blind_queue`, somente campos permitidos, sem resultados automáticos;
- `snapshot/<sha256>` para cada conteúdo selecionado.

Se o total de unidades ou entidades for insuficiente, o estado da seleção
é `insufficient_sample`, a fila cega fica vazia e nenhuma avaliação
pode ser liberada. Os dados brutos excluídos/fora de limite continuam no
armazenamento local, e seus hashes constam do manifesto auditado.

## Integração à barreira de métricas

`guarded_capture_development_evaluate` exige que os bytes do bundle
correspondam aos bytes fornecidos ao `val009_preflight`. Antes de
invocar a barreira anterior, `verify_capture_bundle` relê **todos** os
snapshots e recibos persistidos, inclusive os excluídos, valida a
auditoria/ordem e confere os selecionados contra os payloads. Em seguida
o preflight anterior valida pins, identificação, versão, IDs, amostra,
revisões humanas, freezes e ordem temporal. **Somente depois** pode chamar
o calculador sintético injetado. Os testes incluem espiões que comprovam
zero invocações de métricas nos caminhos de falha.

O verificador não autentica um `TrustedSeal` produzido pelo próprio
operador do ensaio. Hashes e timestamps autoafirmados não substituem
custodiante independente, cofre restrito e testemunho autenticado.

## Limites e próximos gates

1. O adaptador já define a interface explícita para o coletor, mas **não**
   autoriza utilizar relatórios legados que perderam `requested_url`;
   integrar o coletor v23 exige observar o evento na origem.
2. A auditoria do manifesto é pinada pelo `TrustedSeal` quando o
   `evidence_manifest` é pinado; os bytes brutos **não selecionados**
   são comprovados pela releitura do armazenamento local, e ainda não
   são objeto de selagem/retensão externa própria. O futuro selo
   operacional deve incluir o inventário completo, inclusive os não
   selecionados, e impedir perda posterior.
3. A persistência demonstrada em testes usa diretórios temporários:
   não implica que exista cofre privado operacional ou testemunho externo.
4. As exclusões das 117 unidades conhecidas ainda precisam de auditoria
   suplementar para URLs/aliases vistos em desenvolvimento posterior.
5. Permanecem pendentes o manual final, segregação efetiva de funções,
   armazenamento restrito das previsões, selagem das dependências,
   reconciliação controlada dos módulos candidatos v23 e pré-registro
   definitivo, antes de qualquer VAL-009 real.

Os testes são integralmente sintéticos e não alteram VAL-007, CAL-008,
M3 2.2.0, M4 ou seus freezes históricos.
