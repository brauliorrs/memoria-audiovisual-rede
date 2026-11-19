# MAR — Arquitetura definitiva e plano de controle administrativo

**Decisão de engenharia (19/11/2026).** Esta decisão define a arquitetura-alvo; não constitui aprovação científica, autorização de publicação, desbloqueio da Vercel nem implantação da administração em produção. A fase operacional deve observar os gates P0 de recuperação, CI e revisão independente.

## Arquitetura em camadas

1. **Motor científico Python (data plane / autoridade metodológica).** Conectores institucionais, coleta limitada e legalmente autorizada, normalização, deduplicação, cálculo de indicadores, validações por corpus, evidências de origem e instrumentação científica. O motor decide *o que foi observado*; ele não decide sozinho o que pode ser publicado.
2. **PostgreSQL/Neon (control plane / persistência e governança).** Registro tipado de conectores, fila de admissão, estados auditáveis, decisões com atores independentes, proveniência de versões, histórico dos ciclos e dos pacotes científicos. Registros técnicos, aprovações científicas e permissões de publicação são entidades separadas. O Git mantém código, contratos e manifests versionados; Neon mantém o estado operacional com auditoria.
3. **Gerador científico Python de projeções (publication plane).** Reconstitui **todo o pacote** de índices/painéis/agregados elegíveis na mesma epoch a partir de insumos versionados. Produz manifesto de arquivos, conjunto fechado de corpora, referências de aprovação, SHA-256 por entrada e saída, hash da epoch, versão de regras e commit. Staging isolado e verificação atômica; nunca sobrescrever produção ao falhar parcialmente.
4. **Next.js/Vercel (consultation plane).** Rotas institucionais e científicas pré-renderizadas, URLs indexáveis PT/EN/ES, visualizações e consultas exclusivamente aos artefatos aprovados. A forma estática continua adequada para leitura pública; a presença de um corpus no Neon **não** equivale a sua exibição. Somente promover o pacote integral após os gates de validação, curadoria, direitos, integridade e CI. O acesso público segue bloqueado até autorização expressa.
5. **Área administrativa protegida (control plane UI transversal).** Interface de observação e ação limitada sobre fila de admissão, estágios de validação, HOLD, ciclos, frescor dos painéis, divergências de epochs, erros de atualização, evidências e trilha de auditoria. Não expor chaves ou credenciais ao navegador; nunca executar coleta diretamente no request; nunca permitir publicação por botão sem workflow científico e revisão independente.

## Fronteiras que não podem ser confundidas

- `connector_registered` não é `source_validated`; `admission_ready` não é `publication_authorized`; `media_access_observed` não é licença de reprodução.
- O registro `mar_corpora.current_status` atualmente testado na branch Neon de laboratório é **declarativo**; não certifica aceitação científica ou autorização de publicar. Não tratar o laboratório como o Neon principal.
- A fila europeia é gerada pelo motor em `observatorio_fila_pesquisa_europa.csv` e `observatorio_proximos_candidatos_inclusao.json`; sincronizá-la com o banco requer job Python idempotente, com lote/versão e carimbo de origem. Não criar segunda fila concorrente na interface.
- Apenas estados derivados do motor e decisões humanas registradas com proveniência podem avançar. A interface administrativa exibe decisões; a transição autorizada ocorre exclusivamente por API de comando controlada ou execução Python versionada, nunca por `UPDATE` arbitrário.
- A base do observatório pode evoluir antes do site. O painel exibe `scientific_epoch`, `site_epoch`, `last_good_release`, `last_cycle` e o estado `OUT_OF_SYNC / HOLD`; essa diferença **bloqueia promoção**, sem eliminar o snapshot anterior íntegro.

## Publicação atômica

```text
Python collect/normalize --> evidência e staging privado
                            |
                            v
Neon: fila + auditoria + validação + revisão independente
                            |
               gate científico e de publicação
                            |
                            v
Python projection compiler --> pacote completo + manifesto + hashes
                            |
                   testes e aprovação de PR
                            |
                            v
GitHub Actions --> projeto Vercel existente (implantação protegida)
                            |
                            v
Next.js público: somente último pacote integral aprovado
```

Cada nova incorporação científica provoca o planejamento de uma nova versão coerente de todas as projeções aplicáveis: relatórios, recortes, índices, comparações, perfis institucionais, nuvem de palavras e fichas individuais **somente quando autorizadas**. Validação de equivalência entre dados de origem, SQL, arquivos e HTML. Falha ou alteração incompleta => estado HOLD e manutenção do último pacote íntegro. Não fazer refresh independente da nuvem de palavras contornando o manifesto de epoch.

## Administração: estratégia de baixo custo e evolução segura

- **Reaproveitar PR #99**, que implementa protótipo privado de painel Streamlit somente leitura e migrações do esquema `mar_corpora` ensaiadas no Neon de laboratório; não duplicar a máquina de estados do motor universal do PR #98.
- **Não migrar diretamente o esquema experimental para `main` do Neon.** Primeiro completar prova de restauração P0, revisar guards de atores independentes e concessões de papéis LOGIN somente-leitura, testar regressões; depois executar migração aditiva separada com rollback documentado.
- Para a interface final **dentro do mesmo projeto Next.js/Vercel**, será necessário abandonar a exportação global `output: "export"` e adotar renderização híbrida: páginas de consulta públicas continuando estáticas e somente `/admin` + endpoints internos autorizados dinâmicos. Essa mudança precisa de PR, build e aprovação específicos; não altera o acesso público por si só.
- Usar **Neon Auth existente**, sessão verificada no servidor, allowlist explícita de IDs administrativos, política de menor privilégio, antifalsificação para ações, log de operador e recusa por padrão. O Neon Auth atual admite cadastro aberto; endurecer métodos/trusted origins e só habilitar admin após validar as condições de autenticação. O SSO Vercel existente **não substitui** a autorização dentro da aplicação quando as rotas públicas forem abertas.
- O navegador não conecta ao Postgres nem recebe `DATABASE_URL`; servidor lê visões SQL com role `SELECT` restrita e expõe apenas campos autorizados. Comandos de mutação continuam desligados na fase inicial (read-only).
- GitHub Actions existente orquestra testes, exportações e aprovadores; não acrescentar provedor, projeto, domínio, assinatura ou serviço neste MVP. Monitorar os limites de uso dos planos já contratados: reutilização não é garantia de consumo zero.

## Modelo mínimo do painel

1. **Fila científica:** `rank`, `corpus_code`, instituição, origem da proposta, gate pendente, status, evidência/versão e próximo passo. Todos os itens já bloqueados/HOLD permanecem identificados e nunca saem do controle por uma simples filtragem.
2. **Validação:** registro, sonda, evidência validada, curadoria independente, prontidão de admissão, HOLD, revisão de direitos e decisão final de publicação. Cada fase requer ator, prova, data, integridade e estado anterior válido.
3. **Atualizações:** execuções do motor, status por corpus, horário de observação, falhas e retries, SHA do último pacote aprovado, epoch do site e detecção de defasagem.
4. **Auditoria:** trilha somente append, transições inválidas rejeitadas, dependências de PR/CI, prova de rollback e registro das decisões humanas.

## Ordem executiva e critérios de conclusão

1. **Base segura:** revisar e atualizar PR #99 contra a `main` já consolidada, testar a interface isolada com dados de laboratório, revisão por segundo ator; manter main Neon intocada até gate P0.
2. **Governança:** acrescentar persistência idempotente da fila e dos ciclos (proveniência, hash, versão e histórico), sem admitir/publicar automaticamente.
3. **Coerência:** fortalecer o compilador de pacotes B2/B3 já integrado, implementando nova epoch completa com teste real controlado, comparação entre observatório e bundle e rollback funcional.
4. **Admin definitiva:** implementar `/admin` protegida no mesmo site Next.js, migrando a apresentação de PR #99 e reutilizando a API/contratos; habilitar somente após autenticação real, regra de autorização, teste negativo e SQL read-only.
5. **Homologação privada:** simular corpus aprovado, HOLD, crash parcial, falta de credencial, defasagem de epoch e tentativas não autorizadas. Publicar atualização apenas após gates humanos; site permanece privado.
6. **Último passo:** liberar acesso público somente mediante autorização expressa, com perfis privados e backend `/admin` protegidos mesmo após a abertura.

## Situação observada na decisão

- Motor de admissão universal: PR #98 **mesclado** à `main`.
- Governança Neon e painel Streamlit de laboratório: PR #99 **rascunho aberto, não mesclado**; branch principal Neon sem `mar_corpora` verificado nesta auditoria.
- Barreira de snapshot e Arquitetura B1/B2: PRs #121, #123, #124, #125 e #126 **mesclados**; gate de estática vigente; isso não prova automaticamente que um novo corpus possa ser publicado.
- Projeto Vercel `mar-public-site` e Next.js `site/`: existentes; configuração `output: "export"`, sem backend administrativo; não desabilitar proteção de implantação.

**Aceite:** todas as telas e métricas reais estão ligadas à origem, login e autorização foram testados, a fila é reprodutível, uma nova epoch reconstruída é publicada como unidade, HOLD permanece oculto ao público, rollback e CI bloqueiam alterações parciais, e nenhuma credencial ou nova assinatura é requerida além das contas existentes.
