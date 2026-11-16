# MAR — admissão de novas fichas de acervo ao catálogo público (16/11/2026)

## Auditoria de impacto — antes do código

Base `main` em `42a2cd70f401eb33d48a5340952f37979235b09c`. O PR #94 (filtros KAVI) e o PR #93 (segurança P0) permanecem independentes. Nenhuma coleta ou nova publicação é presumida.

### Inventário real por fonte

| Fonte | Evidência existente na main | Decisão para NOVAS fichas |
| --- | --- | --- |
| Eye Filmmuseum (`eye`) | `eye_catalogo_videos_analitico.csv`; snapshot histórico de 15/07/2026 com 630 fichas no catálogo curatorial legado | Evitar duplicação; novas fichas exigem manifesto próprio |
| Czech Television (`czech-television`) | Adaptador e pipeline de coleta existem; não foi encontrado `czech_television_snapshot_metadata.json` na main | HOLD até validação individual/publicação de fichas |
| CICLIC (`ciclic`) | 39 entradas em snapshot histórico de 16/06/2026 | Novas fichas exigem aprovação separada |
| ASIM (`asim`) | 97 entradas em snapshot histórico de 10/06/2026 | Novas fichas exigem aprovação separada |
| Bulgarian NFA (`bnfa`) | Relatórios/outputs legados presentes | Novas fichas exigem aprovação separada |
| Archives Portal Europe (`ape`) | Dados institucionais legados; acesso de novas sondas em HOLD | Proibida admissão incremental enquanto HOLD |

Esses totais históricos não são validações contemporâneas de reprodução, direitos, nem autorização de promover novas páginas.

### Contrato de admissão

1. Lotes adicionais ficam em `data/output/mar_admitted/<corpus>.csv` e `<corpus>.manifest.json`. **Nenhum lote foi fornecido/criado por esta mudança.**
2. Manifesto exige: `schema_version=mar-approved-origin-fiches-v1`, `corpus_code`, `status=approved_public_metadata`, `approved_for_publication=true`, `reviewer` não vazio, `source_run_url` de GitHub Actions, `observed_on`, `record_count`, `catalog_sha256`, `media_downloaded=false`, `viewing_at_origin_only=true`, `corpus_activation=false`. Um manifesto em si **não comprova aprovação humana**; seu PR, fonte e revisão também deverão ser auditados.
3. Cada linha: `source_record_id` único no lote, título e URL `https` oficial da ficha com hostname permitido do corpus, sem URL direta de mídia, sem credenciais, sem query ou fragmento, `media_access_status=unverified`, `media_rights_status=not_verified`, `record_review_status=approved_metadata_only`. Não afirmar vídeo reproduzível.
4. Falha parcial ou corrupção de hash em corpus que possui arquivos causa `HOLD` para o lote: nenhum registro novo dele é admitido.
5. Catálogo público combina somente lotes admitidos; remove colisões com links existentes na mesma unidade, preservando os registros legados e mantendo o nome da origem. Sem escrita no CSV histórico nem acionamento de crawler.
6. Não confiar só no nome/flag do arquivo: comparar SHA, IDs, hosts, estado de publicação e políticas de acesso. `ape` continua bloqueado.

### Testes antes do código

C1: sem arquivos de admissão, resultado vazio, nenhuma publicação tácita.
C2: CSV e manifesto consistentes, origem institucional, aprovação explícita: registros documentais admitidos.
C3: corrupção, ausência unilateral, campo inválido ou duplicação: rejeitar em modo fail-closed.
C4: mídia direta mp4/m3u8, host não permitido, URL com query/fragmento, status de reprodução falsamente verificado: rejeitar.
C5: `ape` rejeitado independentemente de manifesto; `czech-television` sem manifesto segue vazio.
C6: entrada da pesquisa global excluída do filtro **somente vídeos públicos**, sem incrementar alegação de playback.
C7: registros legados Eye permanecem; nova ficha com URL idêntica não duplica no catálogo global.
C8: nenhuma nova chamada HTTP, vídeo, secrets, cron, DB writes ou alteração em CORPORA. Testes existentes e CI completos devem passar.

### Rollback e gates

Reverter import/chamada de `app/streamlit_app.py` e remover módulo/testes novos; todos os datasets originais intocados. O PR fica draft e não faz merge sem Quality Checks e revisão exigida pela branch `main`. Aprovação individual dos primeiros arquivos de cada corpus será tratada em PR específico, nunca fabricada automaticamente.
