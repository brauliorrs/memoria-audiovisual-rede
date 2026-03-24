from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "output"

st.set_page_config(
    page_title="Memoria Audiovisual em Rede",
    layout="wide",
)


def load_csv(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


def render_integrity_badge(value):
    colors = {
        "integro": "#2f7d32",
        "acessivel": "#4c8bf5",
        "suspeito": "#8e44ad",
        "restrito": "#d97706",
        "quebrado": "#c62828",
        "instavel": "#6b7280",
    }
    color = colors.get(str(value), "#6b7280")
    st.markdown(
        f"""
        <div style="display:inline-block;padding:0.3rem 0.7rem;border-radius:999px;
        background:{color};color:white;font-weight:600;font-size:0.9rem;">
        {value}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_vimeo_embed_url(url):
    parsed = urlparse(url)
    if parsed.netloc.lower().startswith("player.vimeo.com") and "/video/" in parsed.path:
        return url
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower().endswith("vimeo.com") and path_parts and path_parts[-1].isdigit():
        return f"https://player.vimeo.com/video/{path_parts[-1]}"
    return None


def build_audiovisual_sites_df(summary_df, links_df):
    ranked = summary_df.loc[summary_df["video_links_found_total"] > 0].copy()

    platforms_df = pd.DataFrame(columns=["slug", "platforms_detectadas"])
    if not links_df.empty:
        platforms_df = (
            links_df.groupby("slug")["platform"]
            .apply(lambda values: ", ".join(sorted(pd.unique(values))))
            .reset_index(name="platforms_detectadas")
        )

    ranked = ranked.merge(platforms_df, on="slug", how="left")
    ranked["platforms_detectadas"] = ranked["platforms_detectadas"].fillna("")

    curated = ranked.sort_values(
        [
            "video_links_found_total",
            "embedded_video_signals_total",
            "integrity_status",
            "institution",
        ],
        ascending=[False, False, True, True],
    )

    return curated[
        [
            "institution",
            "integrity_status",
            "status",
            "video_links_found_total",
            "embedded_video_signals_total",
            "platforms_detectadas",
            "partner_domain",
            "final_url",
            "warning",
            "slug",
        ]
    ]


summary_df = load_csv("iasa_v32_resumo_instituicoes.csv")
links_df = load_csv("iasa_v32_links_video.csv")
internal_df = load_csv("iasa_v32_paginas_internas.csv")

st.title("Plataforma aberta de curadoria e acesso a memoria audiovisual em rede")
st.caption("Primeiro passo: verificar a integridade dos links da IASA e abrir uma pagina de consulta para cada arquivo.")

if summary_df is None:
    st.warning("Nenhum relatorio foi gerado ainda. Execute `python scripts/run_pipeline.py` primeiro.")
    st.stop()

links_df = links_df if links_df is not None else pd.DataFrame(columns=["institution", "slug", "platform", "video_link"])
internal_df = internal_df if internal_df is not None else pd.DataFrame()
if "warning" not in summary_df.columns:
    summary_df["warning"] = ""
if "warning" not in internal_df.columns:
    internal_df["warning"] = ""

query_params = st.query_params
requested_slug = query_params.get("arquivo")
available_slugs = summary_df["slug"].dropna().tolist()
default_slug = requested_slug if requested_slug in available_slugs else available_slugs[0]

sidebar_mode = st.sidebar.radio(
    "Modo",
    options=["Visao geral", "Pagina do arquivo"],
)

st.sidebar.subheader("Arquivo")
selected_slug = st.sidebar.selectbox(
    "Selecione um arquivo da IASA",
    options=available_slugs,
    index=available_slugs.index(default_slug),
    format_func=lambda slug: summary_df.loc[summary_df["slug"] == slug, "institution"].iloc[0],
)
query_params["arquivo"] = selected_slug

selected_summary = summary_df.loc[summary_df["slug"] == selected_slug].iloc[0]
selected_links = (
    links_df.loc[links_df["slug"] == selected_slug]
    .drop_duplicates(subset=["platform", "video_link"])
    .sort_values(["platform", "video_link"])
    .copy()
)

if sidebar_mode == "Visao geral":
    total = len(summary_df)
    with_video = int((summary_df["video_links_found_total"] > 0).sum())
    integral_count = int((summary_df["integrity_status"] == "integro").sum())
    review_count = int(
        summary_df["integrity_status"].isin(["quebrado", "restrito", "instavel", "suspeito"]).sum()
    )
    audiovisual_sites_df = build_audiovisual_sites_df(summary_df, links_df)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Arquivos IASA", total)
    metric_cols[1].metric("Links integros", integral_count)
    metric_cols[2].metric("Precisam revisao", review_count)
    metric_cols[3].metric("Com links de video", with_video)
    tab_dashboard, tab_sites, tab_base = st.tabs(
        ["Painel", f"Sites com links de video ({with_video})", "Base consolidada"]
    )

    with tab_dashboard:
        left, right = st.columns([1.2, 1])

        with left:
            st.subheader("Integridade dos links institucionais")
            integrity_counts = (
                summary_df["integrity_status"]
                .value_counts()
                .rename_axis("integrity_status")
                .reset_index(name="total")
            )
            st.bar_chart(integrity_counts.set_index("integrity_status"))

            st.subheader("Arquivos para revisao")
            review_df = summary_df.sort_values(
                ["priority_review", "video_links_found_total", "embedded_video_signals_total"],
                ascending=[True, False, False],
            )
            st.dataframe(
                review_df[
                    [
                        "institution",
                        "integrity_status",
                        "status",
                        "priority_review",
                        "video_links_found_total",
                        "partner_domain",
                        "warning",
                    ]
                ],
                use_container_width=True,
            )

        with right:
            st.subheader("Plataformas detectadas")
            if not links_df.empty:
                platform_counts = (
                    links_df["platform"]
                    .value_counts()
                    .rename_axis("platform")
                    .reset_index(name="total")
                )
                st.bar_chart(platform_counts.set_index("platform"))
            else:
                st.info("Nenhum link de video foi detectado ainda.")

            st.subheader("Arquivos gerados")
            for file_path in sorted(OUTPUT_DIR.glob("iasa_v32_*")):
                st.write(file_path.name)

    with tab_sites:
        st.subheader(f"Instituicoes com links de video detectados ({with_video})")
        st.caption("Lista direta das instituicoes em que a coleta encontrou pelo menos um link de video.")
        st.dataframe(
            audiovisual_sites_df.drop(columns=["slug"]),
            use_container_width=True,
        )

        for _, row in audiovisual_sites_df.iterrows():
            with st.expander(row["institution"]):
                render_integrity_badge(row["integrity_status"])
                st.write(f"Dominio: {row['partner_domain']}")
                st.write(f"Status tecnico: {row['status']}")
                st.write(f"Links de video: {int(row['video_links_found_total'])}")
                st.write(f"Sinais embutidos: {int(row['embedded_video_signals_total'])}")
                if row["platforms_detectadas"]:
                    st.write(f"Plataformas detectadas: {row['platforms_detectadas']}")
                if pd.notna(row.get("warning")) and str(row.get("warning")).strip():
                    st.warning(str(row["warning"]))
                st.markdown(f"[Abrir site institucional]({row['final_url']})")

    with tab_base:
        st.subheader("Base consolidada")
        integrity_filter = st.multiselect(
            "Filtrar por integridade",
            options=sorted(summary_df["integrity_status"].dropna().unique().tolist()),
            default=sorted(summary_df["integrity_status"].dropna().unique().tolist()),
        )
        filtered = summary_df[summary_df["integrity_status"].isin(integrity_filter)]
        st.dataframe(filtered, use_container_width=True)

else:
    st.subheader(selected_summary["institution"])
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.caption("Integridade")
        render_integrity_badge(selected_summary["integrity_status"])
    with col2:
        st.caption("Status tecnico")
        st.write(selected_summary["status"])
    with col3:
        st.caption("Link institucional")
        st.markdown(f"[{selected_summary['final_url']}]({selected_summary['final_url']})")

    info_cols = st.columns(4)
    info_cols[0].metric("HTTP", selected_summary["http_code"] if pd.notna(selected_summary["http_code"]) else "-")
    info_cols[1].metric("Links de video", int(selected_summary["video_links_found_total"]))
    info_cols[2].metric("Sinais embutidos", int(selected_summary["embedded_video_signals_total"]))
    info_cols[3].metric("Paginas internas", int(selected_summary["candidate_internal_pages"]))

    st.markdown("### Pagina do arquivo")
    if selected_summary["integrity_status"] in {"integro", "acessivel"}:
        st.success("O link institucional respondeu. Esta pagina pode servir como base para a navegacao publica do arquivo.")
    elif selected_summary["integrity_status"] == "suspeito":
        st.warning("O link respondeu, mas a pagina final parece generica ou suspensa. Revise antes de publicar.")
    elif selected_summary["integrity_status"] == "restrito":
        st.warning("O arquivo respondeu com restricao. Pode ser necessario acesso autenticado ou revisao manual.")
    else:
        st.error("O link institucional nao respondeu de forma confiavel. Este arquivo precisa de revisao antes de ser publicado.")

    if pd.notna(selected_summary.get("warning")) and str(selected_summary.get("warning")).strip():
        st.info(str(selected_summary["warning"]))

    st.markdown("### Links de video encontrados")
    if selected_links.empty:
        st.info("Nenhum link de video foi detectado automaticamente para este arquivo.")
    else:
        for _, row in selected_links.iterrows():
            st.markdown(f"**{row['platform']}**")
            st.link_button(f"Abrir {row['video_link']}", row["video_link"])
            if "youtube.com" in row["video_link"] or "youtu.be" in row["video_link"]:
                st.video(row["video_link"])
            else:
                vimeo_embed = get_vimeo_embed_url(row["video_link"])
                if vimeo_embed:
                    components.iframe(vimeo_embed, height=360)
            st.code(row["video_link"], language=None)

    if not internal_df.empty:
        selected_internal = internal_df.loc[internal_df["slug"] == selected_slug]
        if not selected_internal.empty:
            st.markdown("### Paginas internas analisadas")
            st.dataframe(selected_internal, use_container_width=True)
