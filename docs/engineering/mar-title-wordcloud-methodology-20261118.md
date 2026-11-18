# MAR — Nuvem de palavras dos títulos audiovisuais

**Data de introdução:** 18/11/2026  
**Superfície:** página inicial do projeto Vercel existente `mar-public-site` (domínio canônico `https://mar-public-site.vercel.app/`).  
**Escopo:** substituir METADADOS / MEMÓRIA / ORIGEM e os elementos orbitais por uma visualização científica, não por nova publicação de fichas.

## Corpus e método reproduzível

- Script versionado: `scripts/build_mar_title_wordcloud.py`.
- Insumos: 62 catálogos históricos `data/output/*_catalogo_videos_analitico.csv` (gerados na pesquisa Streamlit) e 200 títulos do índice KAVI aprovado.
- Volume: **194.696 linhas de entrada**, **63 fontes**, **83.763 títulos distintos com pelo menos um termo utilizável** no recorte de geração. Os insumos históricos não são uma amostra representativa de toda a produção audiovisual mundial e podem estar incompletos ou desigualmente distribuídos.
- Tokenização multilingue Unicode, normalização casefold, palavras funcionais frequentes de PT/EN/ES/FR/IT/DE/NL/SV/FI, remoção de rótulos genéricos de mídias e meses.
- Uma ocorrência por termo por título, retirando títulos exatamente repetidos dentro de cada corpus; não se somam títulos idênticos de corpora diferentes como se fossem uma única entidade.
- Para reduzir vieses de tamanho, seleção com peso `ln(1 + frequência de títulos distintos) × ln(1 + corpora distintos)`. O tooltip expõe a contagem **não ponderada**, verificável, de títulos e corpora para cada termo.
- São considerados somente termos com **20 ou mais títulos distintos** e presença em **duas ou mais fontes**. A visualização apresenta os 32 primeiros da seleção; os 38 principais integram o arquivo estruturado.
- Cada fonte tem SHA-256 no resumo `site/data/title-wordcloud.json`, conferido pelo gerador e pela CI.

## Limites e segurança de publicação

A nuvem é uma **estatística agregada**, não um catálogo e nem uma licença de metadados. Nenhum título individual, ID, URL, fotograma, imagem, vídeo ou reprodução é incluído na projeção. O catálogo com 200 fichas KAVI autorizadas não sofre mudanças, e fontes históricas ainda sujeitas a HOLD permanecem sem fichas públicas.

A visualização contém palavras nos idiomas originais dos títulos; não são traduzidas artificialmente, pois isso alteraria a frequência lexical. O tamanho das palavras reflete a pontuação de recorrência + distribuição entre fontes, com contagens absolutas ao passar o cursor. A atualização futura deve regenerar o JSON pelo script, revisar os termos e passar pela CI antes de um novo deploy. Evitar contagens inventadas e listas manuais de palavras.

**Reprodutibilidade:**
```sh
python3 scripts/build_mar_title_wordcloud.py --check
python3 -m unittest discover -s tests -p test_mar_title_wordcloud.py -v
```

A publicação usa o **mesmo projeto** Vercel. A operação Streamlit e os corpora congelados permanecem intocados.


## Atualização automática conforme o MAR cresce

A primeira medição de 18/11/2026 (63 fontes, 194.696 linhas e 83.763 títulos distintos com termos úteis) é apenas **linha de base**, não um teto. A nuvem deve crescer conforme os registros de pesquisa sejam incorporados, sem adicionar palavras manualmente.

**Contrato de integração:** cada nova fonte audiovisual que o motor do MAR incorporar deve gerar ou atualizar o catálogo de títulos versionado `data/output/<codigo>_catalogo_videos_analitico.csv` (com `video_title` e/ou `video_title_display`), ou, no caso das fichas individuais aprovadas, atualizar `site/data/kavi-public.json`. Isso não significa autorizar a publicação das fichas individuais da fonte. Registros existentes apenas em um banco de dados externo, ainda sem exportação versionada para esse contrato, **não entram automaticamente** na nuvem.

O workflow `.github/workflows/mar-wordcloud-refresh.yml` observa novos arquivos CSV e alterações nos já existentes, além do índice KAVI e do próprio gerador. Também admite execução manual e uma verificação periódica semanal. Seu processamento é:

1. Regenerar as frequências a partir de **todas as fontes disponíveis**, incluindo as novas; deduplicar títulos dentro de cada corpus e aplicar os critérios de privacidade e distribuição.
2. Reexecutar testes de expansão e as salvaguardas de não divulgação dos dados originais.
3. Se as frequências não mudaram, encerrar **sem novo commit nem implantação**. Se mudaram, criar ou atualizar apenas um PR de manutenção da nuvem na branch `automation/mar-title-wordcloud`, contendo **exclusivamente** `site/data/title-wordcloud.json`.
4. Solicitar as checagens por despacho explícito (necessário porque PRs criados pelo `GITHUB_TOKEN` não disparam automaticamente outros workflows) e solicitar **auto-merge condicionado** às regras de proteção do repositório. Se o GitHub não permitir auto-merge ou escrita por Actions, a alteração permanece como PR para revisão; **nunca** há push direto à `main` por essa automação.
5. Após o merge aprovado, o conteúdo atualizado fica na `main`. A homepage será atualizada **no mesmo domínio** quando a produção do projeto Vercel existente for implantada. Não são criados novos projetos Vercel ou endereços públicos canônicos.

**Latência e escopo:** trata-se de atualização por incorporação/versionamento e build, não streaming ou consulta direta ao banco em cada visita. O material incorporado precisa primeiro alcançar as fontes versionadas; em seguida, a revisão/CI e o deploy garantem atualização segura. O estado da nuvem é acompanhado pelo arquivo gerado e pelo PR, nunca pela memória do chat. Testes não fixam números antigos de fontes ou títulos.

**Dependência verificada em 18/11/2026:** o projeto existente `mar-public-site` ainda **não consta como projeto vinculado ao GitHub** no inventário de integrações Vercel. O workflow de atualização do GitHub, portanto, não garante sozinho a implantação automática. Para que o ciclo se complete sem intervenções, conectar **o projeto Vercel já existente**, sem criar outro, à origem `brauliorrs/memoria-audiovisual-rede`, com diretório raiz `site` e branch de produção `main`, preservando o domínio `mar-public-site.vercel.app`. Até essa ligação estar confirmada, novas estatísticas validadas podem estar na `main` antes de aparecerem na produção; não declarar atualização do site sem verificar o deploy.
