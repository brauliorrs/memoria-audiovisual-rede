# Elegibilidade do corpus e índice de acesso

## Duas camadas distintas

A plataforma preserva duas populações:

1. **registro de descoberta**: todas as entidades identificadas, inclusive bancos comerciais pagos;
2. **corpus científico**: somente arquivos audiovisuais elegíveis para observação longitudinal e cálculo de indicadores.

Nenhuma entidade descoberta é apagada apenas por ser inelegível. A decisão é registrada por `corpus_status`, `exclusion_reason` e justificativa.

## Bancos comerciais pagos

Bancos pagos de imagens ou vídeos são identificados, classificados e catalogados, mas recebem:

```text
corpus_status = excluded
exclusion_reason = commercial_image_bank | commercial_video_bank
```

Eles não entram:

- no corpus científico;
- nas auditorias periódicas do corpus;
- nos denominadores dos indicadores;
- no índice de acesso.

Essa exclusão evita comparar arquivos patrimoniais e institucionais com serviços comerciais cuja finalidade principal é licenciar conteúdo.

## Índice de acesso aos arquivos audiovisuais

### Pergunta

Qual percentual dos arquivos integrantes do corpus oferece acesso sem cadastro, autenticação, pagamento ou solicitação formal?

### Fórmula

```text
100 × arquivos elegíveis com acesso aberto imediato
      ────────────────────────────────────────────
      arquivos elegíveis avaliáveis
```

### Numerador

Arquivos elegíveis para os quais não foi observada barreira de cadastro, login, pagamento, assinatura, autorização institucional, formulário ou solicitação formal.

### Denominador

Somente arquivos elegíveis cujo parâmetro de restrição pôde ser avaliado. Estados `error`, `not_assessable` e `missing_observation` não são convertidos em ausência de barreira.

### Interpretação

- `100`: todos os arquivos elegíveis avaliáveis oferecem acesso aberto imediato;
- `0`: todos exigem ao menos uma barreira administrativa, comercial ou de autenticação;
- valores intermediários: proporção de abertura direta do corpus.

### Limites

O índice não mede quantidade ou qualidade do acervo, completude dos metadados, estabilidade do portal, existência de API ou interoperabilidade. Mede exclusivamente a ausência observada de barreiras imediatas ao acesso.

## Motivo da escolha

O indicador foi preservado da versão anterior porque responde diretamente ao problema central da plataforma: a disponibilidade pública efetiva da memória audiovisual. Indicadores técnicos explicam como os sistemas operam; o índice de acesso mostra se o público consegue chegar ao acervo sem mediação administrativa ou comercial.
