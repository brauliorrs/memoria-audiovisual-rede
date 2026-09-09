# Integração permanente da infraestrutura científica

A seção **Infraestrutura científica** é parte oficial da aplicação Streamlit.

## Decisão arquitetural

- A integração deve permanecer diretamente em `app/streamlit_app.py`.
- Workflows de GitHub Actions não podem editar o código-fonte da interface.
- Workflows são reservados a validação, testes, geração de artefatos e publicação.
- A interface deve carregar catálogo, metodologia, estado operacional, resultados e snapshots, proveniência, evidências e integridade.
- Ausência de artefatos materializados deve ser apresentada explicitamente, sem converter metodologia em resultado empírico.

## Proteção

Um teste permanente verifica o import, a aba, a chamada do renderizador e os índices da navegação. A integração temporária usada para aplicar esta decisão deve ser removida no mesmo commit que consolida o estado definitivo.
