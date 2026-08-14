"""Painel metodológico público do T2A.

A interface resume o protocolo canônico documentado em
``docs/digital-infrastructure-alignment/t2a_ai_post_baseline_validation.md``.
Não apresenta previsões experimentais como resultados oficiais.
"""

from __future__ import annotations

import streamlit as st

_COPY = {
    "pt": {
        "title": "Metodologia de validação da inteligência artificial",
        "intro": (
            "Os componentes de IA são avaliados depois do congelamento do baseline oficial. "
            "Cada unidade corresponde a uma afirmação observável e recebe revisão humana "
            "independente da previsão automática."
        ),
        "automation": (
            "A calibração humana valida o motor por amostragem; ela não representa verificação manual "
            "exaustiva de cada item ou instituição. Depois de validado, o motor opera automaticamente "
            "e pode manter erros residuais de detecção."
        ),
        "answers": "Respostas permitidas: Sim, Não e Não foi possível avaliar.",
        "exception": (
            "‘Não foi possível avaliar’ é usado somente quando a evidência necessária está "
            "inacessível, removida, bloqueada ou tecnicamente insuficiente."
        ),
        "scope": "Superfície institucional observada",
        "scope_text": (
            "A unidade de observação não é apenas a homepage. O protocolo pode seguir páginas internas "
            "e subdomínios da mesma instituição para localizar acervo, pesquisa, metadados, tecnologia, "
            "projetos e documentação pública."
        ),
        "scope_limits": (
            "Padrão experimental: até 2 níveis e 24 páginas por instituição, com timeout, limite de tamanho, "
            "respeito a robots.txt e permanência no domínio institucional."
        ),
        "scope_safety": (
            "São analisados somente conteúdos públicos entregues ao navegador: HTML, metadados, JSON-LD, "
            "links e estruturas públicas de mídia. A plataforma não acessa código de servidor, não usa "
            "credenciais e não contorna login, CAPTCHA, paywall ou geoblocking."
        ),
        "q1": "1. Uso institucional de IA",
        "q1_question": (
            "A instituição declara publicamente utilizar inteligência artificial em alguma "
            "atividade relacionada ao seu acervo audiovisual?"
        ),
        "q1_yes": (
            "Sim: existe declaração institucional explícita e contextualizada. O detector exige sinal de IA "
            "+ contexto de acervo audiovisual + atividade como catalogação, metadados, transcrição, "
            "reconhecimento, restauração, busca, classificação ou segmentação."
        ),
        "q1_no": (
            "Não: nenhuma declaração explícita foi localizada nas superfícies delimitadas. Tecnologia, "
            "automação, analytics, chatbot, API ou biblioteca cliente, isoladamente, não comprovam uso de IA."
        ),
        "q2": "2. Registros públicos de acervo audiovisual",
        "q2_question": (
            "A superfície pública analisada apresenta registros identificáveis de obras ou "
            "documentos audiovisuais pertencentes ao acervo da instituição?"
        ),
        "q2_yes": (
            "Sim: existe ao menos um registro com título, descrição, data, duração, autoria, "
            "identificador, miniatura ou ficha catalográfica audiovisual."
        ),
        "q2_no": (
            "Não: há apenas informação institucional, notícias, fotografias, menção abstrata ao acervo "
            "ou formulário de solicitação sem registros públicos consultáveis."
        ),
        "q3": "3. Vídeo publicamente reproduzível",
        "q3_question": (
            "A superfície analisada permite reproduzir publicamente pelo menos um conteúdo audiovisual do acervo?"
        ),
        "q3_yes": (
            "Sim: há player funcional, link direto ou incorporação externa. Restrição geográfica pode continuar "
            "sendo Sim quando a reprodução pública for confirmada em outra região e a condição for registrada."
        ),
        "q3_no": (
            "Não: existem somente fichas, miniaturas, player inativo, solicitação formal, acesso presencial, "
            "cadastro/login exigido para iniciar a reprodução, vídeo sem relação com o acervo ou link quebrado."
        ),
        "access": (
            "Condições de acesso são registradas separadamente, por exemplo: open_online, geo_restricted, "
            "paid, registration_required, restricted_online e onsite_only."
        ),
        "metrics": "Como o desempenho é calculado",
        "metrics_text": (
            "Somente pares binários comparáveis entram na matriz de confusão. A plataforma calcula verdadeiros "
            "e falsos positivos e negativos, precisão, revocação e F1, com cortes por tarefa, idioma, geografia "
            "e tipo institucional. Casos não avaliáveis, erros e previsões ausentes são reportados separadamente."
        ),
        "separation": (
            "Essas métricas e a exploração ampliada avaliam componentes experimentais. Elas não alteram os 55 corpora, "
            "os nove indicadores ou qualquer resultado do baseline operacional T2."
        ),
    },
    "en": {
        "title": "Artificial-intelligence validation methodology",
        "intro": "AI components are assessed after the official baseline is frozen. Each unit is an observable claim independently reviewed by a human.",
        "automation": "Human calibration validates the engine by sampling; it is not exhaustive manual verification of every item or institution. Once validated, the engine runs automatically and residual detection errors may remain.",
        "answers": "Allowed answers: Yes, No, and Not assessable.",
        "exception": "Not assessable is restricted to inaccessible, removed, blocked, or technically insufficient evidence.",
        "scope": "Observed institutional surface",
        "scope_text": "The unit of observation is not limited to the homepage. The protocol may follow internal pages and institutional subdomains to find collection, research, metadata, technology, project, and documentation evidence.",
        "scope_limits": "Experimental default: up to 2 levels and 24 pages per institution, with timeouts, response-size limits, robots.txt compliance, and institutional-domain scoping.",
        "scope_safety": "Only public client-delivered content is assessed: HTML, metadata, JSON-LD, links, and public media structures. The platform does not access server code, use credentials, or bypass login, CAPTCHA, paywalls, or geoblocking.",
        "q1": "1. Institutional use of AI",
        "q1_question": "Does the institution publicly state that it uses artificial intelligence in an activity related to its audiovisual collection?",
        "q1_yes": "Yes: an explicit institutional statement is contextually linked to AI + an audiovisual collection + an operation such as cataloguing, metadata, transcription, recognition, restoration, search, classification, or segmentation.",
        "q1_no": "No: no explicit statement was found within the delimited surfaces. Technology, automation, analytics, chatbots, APIs, or client libraries alone are insufficient.",
        "q2": "2. Public audiovisual collection records",
        "q2_question": "Does the assessed public surface display identifiable records of audiovisual works or documents from the institution's collection?",
        "q2_yes": "Yes: at least one audiovisual record contains a title, description, date, duration, creator, identifier, thumbnail, or catalogue entry.",
        "q2_no": "No: only institutional information, news, photographs, abstract collection references, or request forms without public records are present.",
        "q3": "3. Publicly playable video",
        "q3_question": "Does the assessed surface allow at least one collection video to be played publicly?",
        "q3_yes": "Yes: a working player, direct playback link, or external embed starts the content. Geoblocking can remain Yes when public playback is verified in another region and the condition is recorded.",
        "q3_no": "No: only records or thumbnails exist, or playback requires a formal request, onsite access, registration/login, non-public authentication, or is broken.",
        "access": "Access conditions are stored separately, including open_online, geo_restricted, paid, registration_required, restricted_online, and onsite_only.",
        "metrics": "How performance is calculated",
        "metrics_text": "Only comparable binary pairs enter the confusion matrix. Precision, recall, F1, false positives, and false negatives are reported by task, language, geography, and institutional type.",
        "separation": "These metrics and the expanded surface exploration assess experimental components and do not change the T2 operational baseline, its 55 corpora, or its nine official indicators.",
    },
    "es": {
        "title": "Metodología de validación de la inteligencia artificial",
        "intro": "Los componentes de IA se evalúan después de congelar la línea base oficial. Cada unidad es una afirmación observable revisada independientemente por una persona.",
        "automation": "La calibración humana valida el motor por muestreo; no representa una verificación manual exhaustiva de cada ítem o institución. Una vez validado, el motor opera automáticamente y puede mantener errores residuales.",
        "answers": "Respuestas permitidas: Sí, No y No fue posible evaluar.",
        "exception": "No fue posible evaluar se limita a evidencia inaccesible, eliminada, bloqueada o técnicamente insuficiente.",
        "scope": "Superficie institucional observada",
        "scope_text": "La unidad de observación no se limita a la página principal. El protocolo puede seguir páginas internas y subdominios institucionales para localizar acervo, investigación, metadatos, tecnología, proyectos y documentación pública.",
        "scope_limits": "Predeterminado experimental: hasta 2 niveles y 24 páginas por institución, con timeout, límite de tamaño, respeto de robots.txt y permanencia en el dominio institucional.",
        "scope_safety": "Solo se analiza contenido público entregado al navegador: HTML, metadatos, JSON-LD, enlaces y estructuras públicas de medios. La plataforma no accede a código de servidor, no usa credenciales ni elude login, CAPTCHA, paywall o geobloqueo.",
        "q1": "1. Uso institucional de IA",
        "q1_question": "¿La institución declara públicamente que utiliza inteligencia artificial en alguna actividad relacionada con su acervo audiovisual?",
        "q1_yes": "Sí: existe una declaración institucional explícita y contextualizada. El detector exige IA + contexto de acervo audiovisual + una operación como catalogación, metadatos, transcripción, reconocimiento, restauración, búsqueda, clasificación o segmentación.",
        "q1_no": "No: no se encontró una declaración explícita en las superficies delimitadas. Tecnología, automatización, analytics, chatbot, API o bibliotecas cliente no son suficientes por sí solos.",
        "q2": "2. Registros públicos del acervo audiovisual",
        "q2_question": "¿La superficie pública analizada presenta registros identificables de obras o documentos audiovisuales del acervo institucional?",
        "q2_yes": "Sí: existe al menos un registro con título, descripción, fecha, duración, autoría, identificador, miniatura o ficha catalográfica audiovisual.",
        "q2_no": "No: solo hay información institucional, noticias, fotografías, referencias abstractas al acervo o formularios sin registros públicos consultables.",
        "q3": "3. Vídeo reproducible públicamente",
        "q3_question": "¿La superficie analizada permite reproducir públicamente al menos un contenido audiovisual del acervo?",
        "q3_yes": "Sí: existe un reproductor funcional, enlace directo o inserción externa. El geobloqueo puede seguir siendo Sí cuando la reproducción pública se confirma en otra región y se registra la condición.",
        "q3_no": "No: solo existen fichas o miniaturas, o la reproducción exige solicitud formal, acceso presencial, registro/login, autenticación no pública o está rota.",
        "access": "Las condiciones de acceso se registran por separado: open_online, geo_restricted, paid, registration_required, restricted_online y onsite_only.",
        "metrics": "Cómo se calcula el desempeño",
        "metrics_text": "Solo los pares binarios comparables entran en la matriz de confusión. Se calculan precisión, exhaustividad, F1, falsos positivos y falsos negativos por tarea, idioma, geografía y tipo institucional.",
        "separation": "Estas métricas y la exploración ampliada evalúan componentes experimentales y no modifican la línea base T2, sus 55 corpus ni sus nueve indicadores oficiales.",
    },
}


def render_t2a_methodology_panel(*, language: str = "pt") -> None:
    """Render the public, localized T2A protocol."""
    text = _COPY.get(language, _COPY["pt"])
    with st.expander(text["title"], expanded=False):
        st.write(text["intro"])
        st.caption(text["automation"])
        st.info(f"{text['answers']} {text['exception']}")
        st.markdown(f"#### {text['scope']}")
        st.write(text["scope_text"])
        st.write(text["scope_limits"])
        st.caption(text["scope_safety"])
        for prefix in ("q1", "q2", "q3"):
            st.markdown(f"#### {text[prefix]}")
            st.markdown(f"**{text[prefix + '_question']}**")
            st.write(text[prefix + "_yes"])
            st.write(text[prefix + "_no"])
        st.caption(text["access"])
        st.markdown(f"#### {text['metrics']}")
        st.write(text["metrics_text"])
        st.warning(text["separation"])


__all__ = ["render_t2a_methodology_panel"]
