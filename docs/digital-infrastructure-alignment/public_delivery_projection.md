# Projeção de entrega das publicações vigentes

## Objetivo

Separar as versões históricas e curatoriais da camada estável de consumo. O registro `active_publications.json` define qual versão está vigente para cada snapshot; a projeção de entrega resolve essas referências e gera arquivos próprios para futuros dashboard, API, exportadores ou pacotes de dados.

## Produtos

```text
data/digital_infrastructure/public/delivery/
├── events.json
└── manifest.json
```

`events.json` reúne apenas os eventos das versões atualmente ativadas. Cada evento recebe `active_publication_id`, preservando a origem editorial utilizada.

O manifesto registra, por snapshot:

- publicação vigente;
- tipo inicial ou revisão;
- número da revisão, quando aplicável;
- caminho histórico de origem;
- quantidade de eventos;
- hash SHA-256 do conteúdo;
- data da ativação.

## Garantias

A projeção:

- não modifica versões iniciais nem revisões;
- não escolhe automaticamente qual versão deve estar vigente;
- falha quando o registro aponta para arquivo ausente;
- falha quando a contagem registrada diverge do conteúdo;
- rejeita eventos associados a outro snapshot;
- grava os produtos por substituição atômica.

## Execução

```bash
python scripts/build_digital_infrastructure_public_delivery.py
```

Também é possível escolher outra saída:

```bash
python scripts/build_digital_infrastructure_public_delivery.py \
  --public-root data/digital_infrastructure/public \
  --output-root data/digital_infrastructure/public/delivery
```

A existência da projeção não representa implantação externa. Ela apenas oferece um contrato estável de leitura para a futura camada pública da plataforma.
