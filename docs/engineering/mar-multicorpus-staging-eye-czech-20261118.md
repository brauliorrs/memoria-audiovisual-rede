# MAR — Normalização multícorpus isolada (18/11/2026)

## Escopo deste incremento
Este incremento cria somente **staging documental offline**, iniciando por Eye Filmmuseum e depois Czech Television. Não publica nenhum registro adicional no Next.js, não modifica o Streamlit, não reexecuta coletas, não altera os corpora científicos congelados e não ativa Neon nem mecanismos de mídia.

## Contrato do importador
Entrada: CSVs analíticos históricos, **somente leitura**:
- `data/output/eye_catalogo_videos_analitico.csv`;
- `data/output/czech_tv_catalogo_videos_analitico.csv`.

Saída: projeção JSON de candidatos contendo identificador determinístico por URL de origem, título, ano quando identificável, tema/assunto, instituição, país, URL oficial e SHA-256 do CSV de entrada. O identificador é derivado da URL, e não deve ser confundido com identificador patrimonial institucional.

**Restrições inegociáveis:** sem download de vídeos, players, consultas a bancos, crawling ou atualização de `site/data/`. Os dados antigos não são escritos. Todos os candidatos têm `publicationApproved=false`, `publicationBlocked=true`, direitos e reprodução não verificados. `sourceRows` mede linhas no CSV, nunca o tamanho do acervo institucional.

## Operação
```bash
python -m unittest discover -s tests -p 'test_mar_multicorpus_staging.py' -v
python scripts/import_mar_multicorpus.py --corpus eye --limit 2
python scripts/import_mar_multicorpus.py --corpus czech --limit 2
python scripts/import_mar_multicorpus.py --corpus eye --limit 0 --output /tmp/mar-eye-candidates.json
python scripts/import_mar_multicorpus.py --corpus czech --limit 0 --output /tmp/mar-czech-candidates.json
python scripts/check_mar_site_index.py
```

O último comando permanece independente e continua verificando as 200 fichas KAVI previamente autorizadas. O destino de saída é opt-in, não pode estar em `site/` e não sobrescreve evidências existentes. O limite padrão é 2 registros.

## Gate de homologação (não executado por este incremento)
**Eye primeiro, Czech depois.** Para promover cada corpus, são necessários:
1. conferência humana de registros amostrados com as fichas institucionais de origem, acessibilidade e estabilidade das URLs;
2. conferência de duplicação, normalização, completude e eventuais mudanças de rota desde o snapshot histórico (Eye julho/2026; Czech julho/2026);
3. identificação de direitos, permissões de republicação dos *metadados* e registro de limites de cobertura;
4. manifesto específico **aprovado** com revisão, versão e checksum e gate independente que compare entrada, projeção e autorização;
5. testes Next.js, auditoria da busca, páginas estáticas e deploy Preview com rollback;
6. aprovação formal antes de qualquer adição ao índice público.

Nenhum desses gates pode ser inferido do simples fato de existir um CSV antigo ou de uma CI ter passado. Eye e Czech permanecem não publicados até emissão de um novo contrato de admissão.

**Status nesta branch:** importador e pilotos automáticos propostos; homologação científica e publicação pendentes. Streamlit permanece disponível.
