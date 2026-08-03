# Memória Audiovisual em Rede

**Plataforma aberta para mapear, monitorar e analisar a presença pública de acervos audiovisuais em plataformas, arquivos, cinematecas e agregadores digitais.**

> Esta versão em português preserva a apresentação original do projeto enquanto o `README.md` principal passa a funcionar como porta de entrada internacional.

O projeto combina coleta automatizada, curadoria metodológica, indicadores comparáveis e visualização em Streamlit para estudar como a memória audiovisual circula, aparece, desaparece, torna-se restrita ou permanece pouco visível em ambientes digitais.

A versão pública está disponível em:

https://memoria-audiovisual-rede-vcxnq9xh7b7uifydhwjxcy.streamlit.app/

## Eixo científico

Pergunta orientadora:

**Sob quais condições infraestruturais, institucionais, técnicas e culturais os acervos audiovisuais se tornam visíveis, invisíveis, restritos ou instáveis em ambientes digitais?**

A plataforma observa rotas públicas, regimes de acesso, padrões de metadados, interoperabilidade, APIs, plataformas externas, infraestrutura tecnológica, sinais de uso de inteligência artificial e mudanças longitudinais.

## Princípios metodológicos

- separação entre descoberta, classificação e elegibilidade do corpus;
- observação longitudinal por snapshots;
- proveniência de cada registro;
- revisão humana de eventos sensíveis;
- preservação do histórico de alterações;
- indicadores científicos versionados;
- exclusão de bancos comerciais pagos do corpus analítico, sem apagá-los do registro de descoberta;
- transparência sobre limites, completude e estabilidade das rotas de coleta.

## Índice de acesso aos arquivos audiovisuais

O índice mede o percentual de arquivos elegíveis cujo acervo é acessível sem cadastro, autenticação, pagamento ou solicitação formal.

Bancos comerciais pagos são identificados e catalogados, mas não entram no corpus científico nem no denominador do índice.

## Estado atual

O projeto está na fase de **validação operacional**. O núcleo arquitetural, os mecanismos de proveniência, os snapshots, a memória longitudinal, a revisão humana e o motor analítico já foram implementados. A etapa atual verifica o comportamento dos detectores e indicadores em observações reais.

## Documentação científica

A documentação internacional está organizada em:

- [`README.md`](README.md) — apresentação principal em inglês;
- [`docs/research/README.md`](docs/research/README.md) — índice do Research Handbook;
- [`docs/research/00_introduction.md`](docs/research/00_introduction.md) — introdução;
- [`docs/research/01_research_problem.md`](docs/research/01_research_problem.md) — problema científico.

## Execução local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Autor

**Bráulio Roberto Rangel da Silva**  
Doutor em Ciências da Comunicação  
Instituto Federal da Paraíba, Brasil
