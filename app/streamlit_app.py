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
        "sem_site": "#475569",
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


def build_detected_sites_df(summary_df, links_df):
    ranked = summary_df.loc[summary_df["video_links_found_total"] > 0].copy()

    if ranked.empty:
        return ranked

    platforms_df = pd.DataFrame(columns=["slug", "platforms_detectadas"])
    if not links_df.empty:
        platforms_df = (
            links_df.groupby("slug")["platform"]
            .apply(lambda values: ", ".join(sorted(pd.unique(values))))
            .reset_index(name="platforms_detectadas")
        )

    ranked = ranked.merge(platforms_df, on="slug", how="left")
    ranked["platforms_detectadas"] = ranked["platforms_detectadas"].fillna("")

    return ranked.sort_values(
        [
            "video_links_found_total",
            "embedded_video_signals_total",
            "integrity_status",
            "institution",
        ],
        ascending=[False, False, True, True],
    )


def build_geography_summaries(df):
    if df.empty:
        return (
            pd.DataFrame(columns=["continent", "instituicoes"]),
            pd.DataFrame(columns=["country", "instituicoes"]),
        )

    continent_counts = (
        df["continent"]
        .fillna("Nao classificado")
        .replace("", "Nao classificado")
        .value_counts()
        .rename_axis("continent")
        .reset_index(name="instituicoes")
    )
    country_counts = (
        df["country"]
        .fillna("Nao classificado")
        .replace("", "Nao classificado")
        .value_counts()
        .rename_axis("country")
        .reset_index(name="instituicoes")
    )
    return continent_counts, country_counts


def build_platform_summary(links_df):
    if links_df.empty:
        return pd.DataFrame(columns=["platform", "total"])
    return (
        links_df["platform"]
        .value_counts()
        .rename_axis("platform")
        .reset_index(name="total")
    )


catalog_df = load_csv("ape_instituicoes.csv")
summary_df = load_csv("ape_resumo_instituicoes.csv")
links_df = load_csv("ape_links_video.csv")
internal_df = load_csv("ape_paginas_internas.csv")

st.title("Plataforma aberta de curadoria e acesso a memoria audiovisual em rede")
st.caption(
    "Versao focada no Archives Portal Europe (APE), a partir da lista oficial de instituicoes "
    "com conteudo publicado e da verificacao dos sites externos de cada instituicao."
)

if summary_df is None:
    st.warning("Nenhum relatorio do APE foi gerado ainda. Execute `python scripts/run_pipeline.py` primeiro.")
    st.stop()

catalog_df = catalog_df if catalog_df is not None else pd.DataFrame()
links_df = links_df if links_df is not None else pd.DataFrame(columns=["institution", "slug", "platform", "video_link"])
internal_df = internal_df if internal_df is not None else pd.DataFrame()

for frame in [catalog_df, summary_df, links_df, internal_df]:
    if "archive_type" not in frame.columns:
        frame["archive_type"] = ""
    if "ape_detail_url" not in frame.columns:
        frame["ape_detail_url"] = ""
    if "website_available" not in frame.columns:
        frame["website_available"] = False
    if "country" not in frame.columns:
        frame["country"] = ""
    if "continent" not in frame.columns:
        frame["continent"] = "Nao classificado"
    if "warning" not in frame.columns:
        frame["warning"] = ""

if summary_df.empty:
    st.warning(
        "O relatorio do APE foi gerado, mas veio sem instituicoes. Revise a execucao do "
        "`scripts/run_pipeline.py` e confira o arquivo `data/output/ape_relatorio.txt`."
    )
    st.stop()

query_params = st.query_params
requested_slug = query_params.get("instituicao")
available_slugs = summary_df["slug"].dropna().tolist()
if not available_slugs:
    st.warning(
        "O relatorio do APE nao trouxe slugs de instituicao. Revise o CSV "
        "`data/output/ape_resumo_instituicoes.csv` antes de abrir a interface."
    )
    st.stop()

default_slug = requested_slug if requested_slug in available_slugs else available_slugs[0]

sidebar_mode = st.sidebar.radio(
    "Modo",
    options=["Visao geral", "Pagina da instituicao"],
)

st.sidebar.subheader("Instituicao")
selected_slug = st.sidebar.selectbox(
    "Selecione uma instituicao do APE",
    options=available_slugs,
    index=available_slugs.index(default_slug),
    format_func=lambda slug: summary_df.loc[summary_df["slug"] == slug, "institution"].iloc[0],
)
query_params["instituicao"] = selected_slug

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
        summary_df["integrity_status"].isin(["quebrado", "restrito", "instavel", "suspeito", "sem_site"]).sum()
    )
    website_count = int(summary_df["website_available"].fillna(False).astype(bool).sum())
    detected_sites_df = build_detected_sites_df(summary_df, links_df)
    continent_counts, country_counts = build_geography_summaries(detected_sites_df)
    platform_counts = build_platform_summary(links_df)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Instituicoes APE", total)
    metric_cols[1].metric("Com webpage externa", website_count)
    metric_cols[2].metric("Links integros", integral_count)
    metric_cols[3].metric("Com links de video", with_video)

    st.info(
        "Nesta etapa, o APE funciona como base institucional principal. A aplicacao verifica a "
        "ficha da instituicao no portal e depois testa o site externo informado em `Webpage`."
    )

    tab_dashboard, tab_sites, tab_geo, tab_base = st.tabs(
        [
            "Painel",
            f"Instituicoes com links de video ({with_video})",
            "Geografia",
            "Base consolidada",
        ]
    )

    with tab_dashboard:
        left, right = st.columns([1.2, 1])

        with left:
            st.subheader("Integridade dos sites institucionais")
            integrity_counts = (
                summary_df["integrity_status"]
                .value_counts()
                .rename_axis("integrity_status")
                .reset_index(name="total")
            )
            st.bar_chart(integrity_counts.set_index("integrity_status"))

            st.subheader("Instituicoes para revisao")
            review_df = summary_df.sort_values(
                ["priority_review", "video_links_found_total", "embedded_video_signals_total"],
                ascending=[True, False, False],
            )
            st.dataframe(
                review_df[
                    [
                        "institution",
                        "archive_type",
                        "integrity_status",
                        "status",
                        "website_available",
                        "video_links_found_total",
                        "partner_domain",
                        "warning",
                    ]
                ],
                use_container_width=True,
            )

        with right:
            st.subheader("Plataformas detectadas")
            if not platform_counts.empty:
                st.bar_chart(platform_counts.set_index("platform"))
            else:
                st.info("Nenhum link de video foi detectado ainda.")

            st.subheader("Arquivos gerados")
            for file_path in sorted(OUTPUT_DIR.glob("ape_*")):
                st.write(file_path.name)

            st.metric("Precisam revisao", review_count)

    with tab_sites:
        st.subheader(f"Instituicoes com links de video detectados ({with_video})")
        if detected_sites_df.empty:
            st.info("Nenhum link de video foi detectado ainda nos sites das instituicoes do APE.")
        else:
            st.dataframe(
                detected_sites_df[
                    [
                        "institution",
                        "archive_type",
                        "integrity_status",
                        "video_links_found_total",
                        "embedded_video_signals_total",
                        "platforms_detectadas",
                        "country",
                        "continent",
                        "partner_domain",
                        "warning",
                        "final_url",
                    ]
                ],
                use_container_width=True,
            )

            for _, row in detected_sites_df.iterrows():
                with st.expander(row["institution"]):
                    render_integrity_badge(row["integrity_status"])
                    if pd.notna(row.get("archive_type")) and str(row.get("archive_type")).strip():
                        st.write(f"Tipo de arquivo: {row['archive_type']}")
                    st.write(f"Dominio: {row['partner_domain']}")
                    st.write(f"Status tecnico: {row['status']}")
                    st.write(f"Links de video: {int(row['video_links_found_total'])}")
                    st.write(f"Sinais embutidos: {int(row['embedded_video_signals_total'])}")
                    if row["platforms_detectadas"]:
                        st.write(f"Plataformas detectadas: {row['platforms_detectadas']}")
                    if pd.notna(row.get("warning")) and str(row.get("warning")).strip():
                        st.warning(str(row["warning"]))
                    if pd.notna(row.get("ape_detail_url")) and str(row.get("ape_detail_url")).strip():
                        st.markdown(f"[Abrir ficha no APE]({row['ape_detail_url']})")
                    st.markdown(f"[Abrir site institucional]({row['final_url']})")

    with tab_geo:
        st.subheader("Organizacao geografica das instituicoes com conteudo audiovisual detectado")
        geo_left, geo_right = st.columns(2)

        with geo_left:
            if not continent_counts.empty:
                st.caption("Distribuicao por continente")
                st.bar_chart(continent_counts.set_index("continent"))
            else:
                st.info("Ainda nao ha distribuicao geografica com links de video detectados.")

        with geo_right:
            if not country_counts.empty:
                st.caption("Distribuicao por pais")
                st.bar_chart(country_counts.set_index("country"))

        continent_filter = st.multiselect(
            "Filtrar continentes",
            options=continent_counts["continent"].tolist(),
            default=continent_counts["continent"].tolist(),
        )
        geo_filtered = detected_sites_df[
            detected_sites_df["continent"]
            .fillna("Nao classificado")
            .replace("", "Nao classificado")
            .isin(continent_filter)
        ]
        st.dataframe(
            geo_filtered[
                [
                    "institution",
                    "archive_type",
                    "continent",
                    "country",
                    "integrity_status",
                    "video_links_found_total",
                    "platforms_detectadas",
                    "final_url",
                ]
            ],
            use_container_width=True,
        )

    with tab_base:
        st.subheader("Base consolidada do APE")
        st.caption(
            "Cada linha representa uma instituicao listada no APE com conteudo publicado, complementada "
            "pela verificacao do site externo informado na ficha do portal."
        )
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
        st.caption("Ficha da instituicao no APE")
        if pd.notna(selected_summary.get("ape_detail_url")) and str(selected_summary.get("ape_detail_url")).strip():
            st.markdown(f"[{selected_summary['ape_detail_url']}]({selected_summary['ape_detail_url']})")
        else:
            st.write("-")

    geo_cols = st.columns(4)
    geo_cols[0].metric("Pais", selected_summary["country"] if pd.notna(selected_summary["country"]) and selected_summary["country"] else "-")
    geo_cols[1].metric(
        "Continente",
        selected_summary["continent"] if pd.notna(selected_summary["continent"]) and selected_summary["continent"] else "Nao classificado",
    )
    geo_cols[2].metric(
        "Tipo de arquivo",
        selected_summary["archive_type"] if pd.notna(selected_summary["archive_type"]) and selected_summary["archive_type"] else "-",
    )
    geo_cols[3].metric(
        "Webpage no APE",
        "Sim" if bool(selected_summary.get("website_available")) else "Nao",
    )

    info_cols = st.columns(4)
    info_cols[0].metric("HTTP", selected_summary["http_code"] if pd.notna(selected_summary["http_code"]) else "-")
    info_cols[1].metric("Links de video", int(selected_summary["video_links_found_total"]))
    info_cols[2].metric("Sinais embutidos", int(selected_summary["embedded_video_signals_total"]))
    info_cols[3].metric("Paginas internas", int(selected_summary["candidate_internal_pages"]))

    st.markdown("### Pagina da instituicao")
    if selected_summary["integrity_status"] in {"integro", "acessivel"}:
        st.success("O site externo respondeu. Esta instituicao pode seguir para curadoria publica.")
    elif selected_summary["integrity_status"] == "suspeito":
        st.warning("O site respondeu, mas a pagina final parece generica ou suspensa. Revise antes de publicar.")
    elif selected_summary["integrity_status"] == "restrito":
        st.warning("O site respondeu com restricao. Pode ser necessario acesso autenticado ou revisao manual.")
    elif selected_summary["integrity_status"] == "sem_site":
        st.warning("A ficha no APE nao informa uma webpage externa para esta instituicao.")
    else:
        st.error("O site institucional nao respondeu de forma confiavel. Esta instituicao precisa de revisao.")

    if pd.notna(selected_summary.get("warning")) and str(selected_summary.get("warning")).strip():
        st.info(str(selected_summary["warning"]))

    if pd.notna(selected_summary.get("final_url")) and str(selected_summary.get("final_url")).strip():
        st.markdown("### Site institucional")
        st.markdown(f"[{selected_summary['final_url']}]({selected_summary['final_url']})")

    st.markdown("### Links de video encontrados")
    if selected_links.empty:
        st.info("Nenhum link de video foi detectado automaticamente para esta instituicao.")
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
