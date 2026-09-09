# Memória Audiovisual em Rede

**Plataforma aberta para mapear, monitorar e analisar a presença pública de acervos audiovisuais em plataformas, arquivos, cinematecas e agregadores digitais.**

> Esta versão em português preserva a apresentação original do projeto enquanto o `README.md` principal funciona como porta de entrada internacional.

O projeto combina coleta automatizada, curadoria metodológica, indicadores comparáveis e visualização em Streamlit para estudar como a memória audiovisual circula, aparece, desaparece, torna-se restrita ou permanece pouco visível em ambientes digitais.

A versão pública está disponível em:

https://memoria-audiovisual-rede-hv3dgxwqgaka2i6ahhmb5v.streamlit.app/

## Eixo científico

Pergunta orientadora:

**Sob quais condições infraestruturais, institucionais, técnicas e culturais os acervos audiovisuais se tornam visíveis, invisíveis, restritos ou instáveis em ambientes digitais?**

A plataforma observa rotas públicas, regimes de acesso, padrões de metadados, interoperabilidade, APIs, plataformas externas, infraestrutura tecnológica, sinais públicos relacionados ao uso de inteligência artificial e mudanças longitudinais.

Detectores automáticos produzem evidências que ainda precisam ser interpretadas e, quando sensíveis ou ambíguas, submetidas à revisão humana. Ausência de evidência detectada não comprova ausência institucional do fenômeno observado.

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

O índice mede o percentual de arquivos elegíveis e avaliáveis cujo acervo é acessível sem cadastro, autenticação, pagamento ou solicitação formal.

Bancos comerciais pagos são identificados e catalogados, mas não entram no corpus científico nem no denominador do índice.

## Estado atual

O projeto está na fase de **validação operacional**. O núcleo arquitetural, os mecanismos de proveniência, os snapshots, a memória longitudinal, a revisão humana e o motor analítico já foram implementados. A etapa atual verifica o comportamento dos detectores e indicadores em observações reais.

O sucesso dos testes automatizados confirma a integridade estrutural da implementação, mas não equivale à validação empírica completa dos detectores ou das classificações institucionais.

## Documentação científica

- [`README.md`](README.md) — apresentação principal em inglês;
- [`docs/research/README.md`](docs/research/README.md) — índice do Research Handbook;
- [`docs/research/executive_summary.md`](docs/research/executive_summary.md) — apresentação científica concisa;
- [`docs/DOCUMENTATION_GOVERNANCE.md`](docs/DOCUMENTATION_GOVERNANCE.md) — hierarquia, terminologia e governança editorial;
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — regras de contribuição;
- [`CITATION.cff`](CITATION.cff) — metadados formais de citação;
- [`LICENSE`](LICENSE) — condições de reutilização.

## Execução local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Validação documental:

```powershell
python scripts/check_markdown_links.py
```

## Licenciamento e citação

O código é disponibilizado sob licença MIT. A documentação original e os dados produzidos e publicados pelo projeto são disponibilizados sob CC BY 4.0, sem substituir direitos ou restrições aplicáveis às fontes e aos materiais de terceiros.

Para citar a infraestrutura, use os metadados disponíveis em [`CITATION.cff`](CITATION.cff).

## Autor

**Bráulio Roberto Rangel da Silva**  
Doutor em Ciências da Comunicação  
Instituto Federal da Paraíba, Brasil
