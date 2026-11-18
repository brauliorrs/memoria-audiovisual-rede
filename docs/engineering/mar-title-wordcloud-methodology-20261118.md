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
