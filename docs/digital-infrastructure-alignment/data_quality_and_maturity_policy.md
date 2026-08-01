# Política de qualidade e maturidade dos dados

## Objetivo

Definir como a plataforma avaliará a qualidade, a maturidade e a aptidão de cada registro, conjunto de dados, snapshot, indicador e produto publicado.

A avaliação de qualidade não substitui validação curatorial. Ela organiza evidências sobre a confiabilidade e a utilidade científica dos dados.

## Dimensões de qualidade

Cada objeto poderá ser avaliado nas seguintes dimensões:

- `completeness`: presença dos campos obrigatórios e relevantes;
- `timeliness`: atualidade em relação à janela de revalidação;
- `consistency`: coerência interna, relacional, temporal e semântica;
- `traceability`: capacidade de reconstruir fonte, aquisição, transformação e revisão;
- `evidence_strength`: força e adequação das evidências;
- `coverage`: proporção do universo observável efetivamente avaliada;
- `comparability`: possibilidade de comparação entre instituições, países, períodos e versões;
- `reproducibility`: possibilidade de reproduzir o processo de obtenção e transformação;
- `curatorial_confidence`: confiança resultante da revisão humana;
- `fitness_for_use`: aptidão para uso operacional, científico, longitudinal ou público.

## Escala

Cada dimensão utilizará escala de 0 a 4:

- `0_not_assessed`;
- `1_insufficient`;
- `2_limited`;
- `3_adequate`;
- `4_strong`.

Não haverá preenchimento automático por valor padrão. Dimensão não avaliada permanecerá explicitamente como `0_not_assessed`.

## Níveis de maturidade

- `M0_unregistered`: objeto ainda não incorporado ao modelo de qualidade;
- `M1_observed`: registro bruto ou sinal inicial, sem validação suficiente;
- `M2_structured`: objeto estruturado e vinculado a identificadores e proveniência;
- `M3_reviewed`: revisão humana concluída, com problemas críticos resolvidos;
- `M4_research_ready`: apto para análise científica sob limitações documentadas;
- `M5_publication_ready`: apto para produto público, indicador ou API;
- `M6_longitudinal_ready`: comparável entre períodos e versões de forma documentada.

Os níveis são cumulativos. Um objeto só pode atingir nível superior quando satisfizer os requisitos dos níveis anteriores.

## Princípios

1. Qualidade deve ser avaliada por dimensão, não apenas por nota única.
2. Pontuação agregada não pode ocultar falha crítica.
3. Ausência de dado deve ser distinguida de ausência do fenômeno.
4. Cobertura insuficiente deve limitar interpretação e publicação.
5. Dados maduros podem perder atualidade e requerer revalidação.
6. Correções devem gerar nova versão, sem apagar avaliações anteriores.
7. Aptidão para uso depende do propósito declarado.

## Bloqueios críticos

Independentemente da pontuação agregada, impedem publicação:

- referência relacional inválida;
- ausência de proveniência mínima;
- evidência incompatível com a afirmação;
- conflito temporal não resolvido;
- registro `pending_review` usado como confirmado;
- risco alto ou crítico sem revisão reforçada;
- indicador com denominador ou cobertura instável;
- incompatibilidade de schema não documentada.

## Versionamento

Cada avaliação deverá registrar:

- `quality_assessment_id`;
- `object_type` e `object_id`;
- `object_version_id`;
- `snapshot_id`, quando aplicável;
- `quality_model_version`;
- valores por dimensão;
- nível de maturidade;
- aptidões concedidas ou negadas;
- bloqueios;
- avaliador ou agente;
- data da avaliação;
- data limite de revalidação;
- justificativa e evidências.

## Relação com publicação

Somente objetos classificados como `M5_publication_ready` poderão alimentar produtos públicos desagregados. Objetos `M4_research_ready` poderão ser usados em análise científica interna ou restrita. Comparações históricas exigem `M6_longitudinal_ready` ou declaração explícita de comparabilidade limitada.
