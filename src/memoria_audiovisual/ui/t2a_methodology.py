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
        "answers": "Respostas permitidas: Sim, Não e Não foi possível avaliar.",
        "exception": (
            "‘Não foi possível avaliar’ é usado somente quando a evidência necessária está "
            "inacessível, removida, bloqueada ou tecnicamente insuficiente."
        ),
        "q1": "1. Uso institucional de IA",
        "q1_question": (
            "A instituição declara publicamente utilizar inteligência artificial em alguma "
            "atividade relacionada ao seu acervo audiovisual?"
        ),
        "q1_yes": (
            "Sim: existe declaração institucional explícita sobre catalogação, metadados, "
            "transcrição, reconhecimento, restauração, busca, classificação ou geração/modificação audiovisual."
        ),
        "q1_no": (
            "Não: as superfícies previstas foram examinadas e nenhuma declaração explícita foi localizada. "
            "Tecnologia, automação, analytics, chatbot ou API, isoladamente, não comprovam uso de IA."
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
            "Sim: há player funcional, link direto ou incorporação externa que permite iniciar o conteúdo. "
            "Acesso pago continua sendo Sim, com a condição de acesso registrada separadamente."
        ),
        "q3_no": (
            "Não: existem somente fichas, miniaturas, player inativo, solicitação formal, acesso presencial, "
            "autenticação não pública, vídeo institucional sem relação com o acervo ou link quebrado."
        ),
        "metrics": "Como o desempenho é calculado",
        "metrics_text": (
            "Somente pares binários comparáveis entram na matriz de confusão. A plataforma calcula verdadeiros "
            "e falsos positivos e negativos, precisão, revocação e F1, com cortes por tarefa, idioma, geografia "
            "e tipo institucional. Casos não avaliáveis, erros e previsões ausentes são reportados separadamente."
        ),
        "separation": (
            "Essas métricas avaliam componentes experimentais. Elas não alteram os 55 corpora, os nove indicadores "
            "ou qualquer resultado do baseline operacional T2."
        ),
    },
    "en": {
        "title": "Artificial-intelligence validation methodology",
        "intro": "AI components are assessed after the official baseline is frozen. Each unit is an observable claim independently reviewed by a human.",
        "answers": "Allowed answers: Yes, No, and Not assessable.",
        "exception": "Not assessable is restricted to inaccessible, removed, blocked, or technically insufficient evidence.",
        "q1": "1. Institutional use of AI",
        "q1_question": "Does the institution publicly state that it uses artificial intelligence in an activity related to its audiovisual collection?",
        "q1_yes": "Yes: an explicit institutional statement covers cataloguing, metadata, transcription, recognition, restoration, search, classification, or audiovisual generation/modification.",
        "q1_no": "No: the defined surfaces were examined and no explicit statement was found. Technology, automation, analytics, chatbots, or APIs alone are insufficient.",
        "q2": "2. Public audiovisual collection records",
        "q2_question": "Does the assessed public surface display identifiable records of audiovisual works or documents from the institution's collection?",
        "q2_yes": "Yes: at least one audiovisual record contains a title, description, date, duration, creator, identifier, thumbnail, or catalogue entry.",
        "q2_no": "No: only institutional information, news, photographs, abstract collection references, or request forms without public records are present.",
        "q3": "3. Publicly playable video",
        "q3_question": "Does the assessed surface allow at least one collection video to be played publicly?",
        "q3_yes": "Yes: a working player, direct playback link, or external embed starts the content. Paid public access remains Yes and is recorded separately.",
        "q3_no": "No: only records or thumbnails exist, or playback requires a formal request, onsite access, non-public authentication, or is broken.",
        "metrics": "How performance is calculated",
        "metrics_text": "Only comparable binary pairs enter the confusion matrix. Precision, recall, F1, false positives, and false negatives are reported by task, language, geography, and institutional type.",
        "separation": "These metrics assess experimental components and do not change the T2 operational baseline, its 55 corpora, or its nine official indicators.",
    },
    "es": {
        "title": "Metodología de validación de la inteligencia artificial",
        "intro": "Los componentes de IA se evalúan después de congelar la línea base oficial. Cada unidad es una afirmación observable revisada independientemente por una persona.",
        "answers": "Respuestas permitidas: Sí, No y No fue posible evaluar.",
        "exception": "No fue posible evaluar se limita a evidencia inaccesible, eliminada, bloqueada o técnicamente insuficiente.",
        "q1": "1. Uso institucional de IA",
        "q1_question": "¿La institución declara públicamente que utiliza inteligencia artificial en alguna actividad relacionada con su acervo audiovisual?",
        "q1_yes": "Sí: existe una declaración institucional explícita sobre catalogación, metadatos, transcripción, reconocimiento, restauración, búsqueda, clasificación o generación/modificación audiovisual.",
        "q1_no": "No: se examinaron las superficies previstas y no se encontró una declaración explícita. Tecnología, automatización, analytics, chatbot o API no son suficientes por sí solos.",
        "q2": "2. Registros públicos del acervo audiovisual",
        "q2_question": "¿La superficie pública analizada presenta registros identificables de obras o documentos audiovisuales del acervo institucional?",
        "q2_yes": "Sí: existe al menos un registro con título, descripción, fecha, duración, autoría, identificador, miniatura o ficha catalográfica audiovisual.",
        "q2_no": "No: solo hay información institucional, noticias, fotografías, referencias abstractas al acervo o formularios sin registros públicos consultables.",
        "q3": "3. Vídeo reproducible públicamente",
        "q3_question": "¿La superficie analizada permite reproducir públicamente al menos un contenido audiovisual del acervo?",
        "q3_yes": "Sí: existe un reproductor funcional, enlace directo o inserción externa. El acceso público de pago continúa siendo Sí y se registra por separado.",
        "q3_no": "No: solo existen fichas o miniaturas, o la reproducción exige solicitud formal, acceso presencial, autenticación no pública o está rota.",
        "metrics": "Cómo se calcula el desempeño",
        "metrics_text": "Solo los pares binarios comparables entran en la matriz de confusión. Se calculan precisión, exhaustividad, F1, falsos positivos y falsos negativos por tarea, idioma, geografía y tipo institucional.",
        "separation": "Estas métricas evalúan componentes experimentales y no modifican la línea base T2, sus 55 corpus ni sus nueve indicadores oficiales.",
    },
}


def render_t2a_methodology_panel(*, language: str = "pt") -> None:
    """Render the public, localized T2A protocol."""
    text = _COPY.get(language, _COPY["pt"])
    with st.expander(text["title"], expanded=False):
        st.write(text["intro"])
        st.info(f"{text['answers']} {text['exception']}")
        for prefix in ("q1", "q2", "q3"):
            st.markdown(f"#### {text[prefix]}")
            st.markdown(f"**{text[prefix + '_question']}**")
            st.write(text[prefix + "_yes"])
            st.write(text[prefix + "_no"])
        st.markdown(f"#### {text['metrics']}")
        st.write(text["metrics_text"])
        st.warning(text["separation"])


__all__ = ["render_t2a_methodology_panel"]
