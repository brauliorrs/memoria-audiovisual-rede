# Limites para coleta automatizada

## Regra geral

A plataforma somente deverá coletar conteúdo acessível sem contornar autenticação, bloqueios técnicos, paywalls, CAPTCHAs, controles de sessão ou outras barreiras de acesso.

## Verificações prévias

Cada fonte deverá registrar:

- URL e domínio;
- natureza pública ou restrita da página;
- presença de termos de uso relevantes;
- licença ou indicação de reutilização, quando disponível;
- `robots.txt`, quando aplicável;
- método de acesso disponível;
- limites técnicos ou documentados;
- necessidade de credenciais;
- categoria de dados potencialmente coletada;
- base metodológica para inclusão.

## Métodos permitidos

- API pública documentada;
- endpoint aberto e destinado a consulta;
- download público disponibilizado pela própria instituição;
- páginas públicas acessíveis por navegação ordinária;
- feeds, sitemaps, OAI-PMH, IIIF e outros serviços abertos;
- consulta manual documentada.

## Métodos vedados

- quebra ou evasão de autenticação;
- reutilização não autorizada de credenciais;
- ocultação deliberada de identidade para burlar bloqueios;
- rotação agressiva de IP para superar limites;
- exploração de vulnerabilidades;
- coleta de áreas privadas ou administrativas;
- reprodução integral de conteúdo protegido sem necessidade científica e base documental.

## Proporcionalidade operacional

Os coletores deverão prever:

- identificação clara do agente quando tecnicamente adequado;
- limites de taxa conservadores;
- pausas e retentativas graduais;
- cache e reutilização de respostas;
- interrupção diante de erro persistente;
- registro de data, status HTTP e método;
- prioridade a APIs e exports oficiais sobre scraping de interface.

## Estado de coleta

Cada tentativa deverá ser classificada como:

- `allowed_completed`;
- `allowed_partial`;
- `temporarily_unavailable`;
- `restricted_not_collected`;
- `terms_review_required`;
- `legal_review_required`;
- `collection_suspended`.

Ausência de coleta não deverá ser interpretada como ausência de dados, tecnologia ou relação institucional.