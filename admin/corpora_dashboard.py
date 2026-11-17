"""Internal, read-only MAR corpus-management dashboard.

Run independently: streamlit run admin/corpora_dashboard.py
DO NOT mount into the public Streamlit navigation. Requires server OIDC
configuration, verified email allowlist and a dedicated SELECT-only PG role.
No approval, ingestion, modification, collection or publication action exists.
"""
from __future__ import annotations

import os
import time
from collections.abc import Mapping

import streamlit as st

from memoria_audiovisual.corpus_admission_engine import REGISTRY
from memoria_audiovisual.corpus_registry_pg import (
    list_corpora, list_corpus_events, read_only_role_assertion,
)

STAGES = (
    "", "registered", "probed", "evidence_validated",
    "curator_reviewed", "admission_ready", "HOLD", "note",
)
COLS = (
    "Código", "Instituição", "Tipo de fonte", "Domínios",
    "Último estágio informado", "Evento", "Data do evento",
    "Publicação autorizada pelo banco", "Validação científica provada pelo banco",
)


def authorized_admin(user: object, allowlist: str) -> bool:
    """Require verified, unexpired OIDC identity and a server-side allowlist.

    Streamlit authenticates the identity provider; our application checks
    authorization. Missing or expired identity claims fail closed even if a
    Streamlit login cookie remains valid.
    """
    if not isinstance(allowlist, str) or not allowlist.strip():
        return False
    try:
        if isinstance(user, Mapping):
            logged_in = getattr(user, "is_logged_in", user.get("is_logged_in"))
            verified = user.get("email_verified")
            email = user.get("email")
            expires_at = user.get("exp")
        else:
            logged_in = getattr(user, "is_logged_in", False)
            verified = getattr(user, "email_verified", False)
            email = getattr(user, "email", None)
            expires_at = getattr(user, "exp", None)
    except (AttributeError, KeyError, TypeError):
        return False
    # Unlike Streamlit's 30-day cookie, the OIDC ID-token expiration must
    # be honored for a privileged admin app.
    if type(expires_at) not in (int, float) or expires_at <= time.time():
        return False
    allowed = {item.strip().casefold() for item in allowlist.split(",") if item.strip()}
    return (
        logged_in is True and verified is True
        and isinstance(email, str) and email.casefold().strip() in allowed
    )


def _make_connection(dsn: str):
    import psycopg  # optional admin-only dependency, never needed by public MAR
    # SSL is mandatory in production Neon; SQL statement limit protects service.
    return psycopg.connect(
        dsn, connect_timeout=7,
        options="-c default_transaction_read_only=on -c statement_timeout=5000",
        autocommit=True,
    )


def main() -> None:
    st.set_page_config(page_title="MAR · Gestão de corpora", layout="wide")
    st.title("MAR — Gestão administrativa de corpora")
    st.caption(
        "Cadastro técnico e histórico declarativo de auditoria. "
        "Esta visualização NÃO aprova fontes, direitos, mídias ou publicação."
    )
    allowlist = os.environ.get("MAR_ADMIN_EMAIL_ALLOWLIST", "")
    if not allowlist:
        st.error("Painel indisponível: lista de administradores não configurada.")
        st.stop()
    if not authorized_admin(st.user, allowlist):
        st.warning("Acesso restrito: autenticação OIDC e e-mail verificado exigidos.")
        if not getattr(st.user, "is_logged_in", False):
            if st.button("Entrar com provedor institucional"):
                st.login()
        elif st.button("Encerrar sessão e autenticar novamente"):
            st.logout()
        st.stop()
    dsn = os.environ.get("MAR_CORPORA_READONLY_DATABASE_URL", "")
    if not dsn:
        st.error("Banco de consulta não configurado (credencial exclusivamente de leitura).")
        st.stop()

    search_col, stage_col, page_col = st.columns([3, 2, 1])
    with search_col:
        term = st.text_input("Buscar código ou instituição", max_chars=120)
    with stage_col:
        stage = st.selectbox("Último estágio informado", options=STAGES,
                             format_func=lambda value: value or "Todos")
    with page_col:
        page = st.number_input("Página", min_value=1, value=1, step=1)
    try:
        with _make_connection(dsn) as conn:
            read_only_role_assertion(conn)
            result = list_corpora(
                conn, page=int(page), page_size=25,
                search=term, stage=stage,
            )
            st.metric("Conectores persistidos (filtro atual)", result["total"])
            st.caption(
                f"Página {result['page']} · até {result['page_size']} por página. "
                "Conectores cadastrados não são corpora aprovados."
            )
            display = []
            for row in result["rows"]:
                (code, institution, kind, hosts, reported_stage, event_id, at,
                 publication, scientific) = row
                display.append({
                    COLS[0]: code, COLS[1]: institution, COLS[2]: kind,
                    COLS[3]: ", ".join(hosts or []),
                    COLS[4]: reported_stage or "sem evento",
                    COLS[5]: event_id, COLS[6]: at,
                    COLS[7]: publication, COLS[8]: scientific,
                })
            st.dataframe(display, use_container_width=True, hide_index=True)
            code = st.selectbox("Consultar eventos de uma fonte cadastrada",
                                options=[""] + sorted(REGISTRY),
                                format_func=lambda x: x or "Selecione")
            if code:
                recent = list_corpus_events(conn, code, limit=40)
                st.subheader("Histórico imutável por política do banco")
                st.caption(
                    "Os eventos são declarações rastreáveis, não confirmação "
                    "independente da revisão científica."
                )
                st.dataframe(
                    [{
                        "Evento": row[0], "Estágio": row[1], "Ator declarado": row[2],
                        "SHA-256": row[3], "Referência": row[4],
                        "Observação": row[5], "Registrado em": row[6],
                    } for row in recent],
                    use_container_width=True, hide_index=True,
                )
    except Exception:
        # Never show a database URI, password, SQL query or provider traceback.
        st.error("Não foi possível consultar o banco administrativo com segurança.")
        st.stop()


if __name__ == "__main__":
    main()
