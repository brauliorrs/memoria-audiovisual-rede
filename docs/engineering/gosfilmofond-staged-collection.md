# Gosfilmofond — engenharia staged do catálogo público

**Estado:** coletor staged em validação operacional; não constitui ainda promoção a corpus ativo.

## Evidência técnica

O probe público validou no executor do GitHub:

- `robots.txt` acessível e avaliado segundo semântica RFC 9309;
- `/films/` permitido;
- `/wp-admin/admin-ajax.php` explicitamente permitido;
- `/wp-json/` e certas rotas de paginação/query bloqueadas, portanto não utilizadas;
- interface pública com tamanhos de página 10, 20, 50 e 100;
- `page_count=100` validado;
- duas páginas AJAX consecutivas com 100 registros cada, IDs distintos;
- 598 páginas declaradas pela interface observada.

O catálogo público e fichas individuais expõem metadados cinematográficos, mas a existência de uma ficha não implica streaming público.

## Estratégia staged

O coletor usa somente o mecanismo público `action=filter_films` em `admin-ajax.php`.

Ele:

1. relê `robots.txt` antes da enumeração;
2. abre `/films/` para obter os tamanhos de página declarados;
3. seleciona o maior tamanho público permitido, atualmente 100;
4. estabelece o total de páginas a partir da primeira resposta;
5. percorre sequencialmente as páginas declaradas;
6. deduplica por chave pública `/films/<key>/`;
7. falha em drift do total de páginas, página intermediária curta, duplicações entre páginas ou erro de requisição;
8. não escaneia IDs;
9. não baixa mídia;
10. não usa M3/M4.

## Critério de promoção

A rodada real precisa satisfazer simultaneamente:

- `integrity_status=integro`;
- ao menos 50.000 permalinks públicos únicos;
- ao menos 500 páginas AJAX observadas;
- URLs restritas ao contrato `https://gosfilmofond.ru/films/<key>/`;
- nenhuma página obrigatória com erro;
- snapshot e catálogo com a mesma contagem;
- pipeline/checks e CI completos verdes.

Esses limites não definem tamanho físico do acervo. Servem apenas para impedir que uma coleta truncada seja promovida como representação do catálogo web que, no probe, declarou aproximadamente 598 páginas de 100 registros.

Se o critério falhar, o Gosfilmofond permanece protocolado para reavaliação e a fila avança.
