from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app" / "streamlit_app.py"


@dataclass(frozen=True)
class PageInventory:
    function: str
    start_line: int
    end_line: int
    lines: int
    columns_calls: int
    max_columns: int
    metrics: int
    dataframes: int
    charts: int
    tabs: int
    expanders: int
    buttons: int
    download_buttons: int
    selectors: int
    horizontal_pressure: int
    priority: str
    recommendations: tuple[str, ...]


def call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def literal_column_count(node: ast.Call) -> int:
    if not node.args:
        return 0
    arg = node.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
        return arg.value
    if isinstance(arg, (ast.List, ast.Tuple)):
        return len(arg.elts)
    return 0


def render_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (node.name.startswith("render_") or node.name.startswith("show_"))
    ]


def analyse_function(node: ast.FunctionDef) -> PageInventory:
    counts = {
        "columns": 0,
        "metric": 0,
        "dataframe": 0,
        "chart": 0,
        "tabs": 0,
        "expander": 0,
        "button": 0,
        "download_button": 0,
        "selector": 0,
    }
    max_columns = 0

    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        name = call_name(child)
        if name == "columns":
            counts["columns"] += 1
            max_columns = max(max_columns, literal_column_count(child))
        elif name == "metric":
            counts["metric"] += 1
        elif name in {"dataframe", "data_editor", "table"}:
            counts["dataframe"] += 1
        elif name in {"plotly_chart", "altair_chart", "pyplot", "line_chart", "bar_chart", "area_chart", "scatter_chart", "map"}:
            counts["chart"] += 1
        elif name == "tabs":
            counts["tabs"] += 1
        elif name == "expander":
            counts["expander"] += 1
        elif name in {"button", "link_button"}:
            counts["button"] += 1
        elif name == "download_button":
            counts["download_button"] += 1
        elif name in {"selectbox", "multiselect", "radio", "segmented_control", "pills", "slider", "select_slider"}:
            counts["selector"] += 1

    end_line = getattr(node, "end_lineno", node.lineno)
    line_count = end_line - node.lineno + 1
    pressure = (
        counts["columns"] * 3
        + max(0, max_columns - 2) * 4
        + counts["dataframe"] * 2
        + counts["chart"] * 2
        + counts["tabs"]
        + counts["metric"] // 3
    )

    recommendations: list[str] = []
    if max_columns >= 4:
        recommendations.append("reduzir grupos de quatro ou mais colunas; empilhar métricas em blocos de duas ou em fluxo vertical")
    elif max_columns == 3:
        recommendations.append("validar quebra responsiva das estruturas de três colunas")
    if counts["dataframe"] >= 3:
        recommendations.append("priorizar tabelas verticais, resumos iniciais e detalhamento sob demanda")
    if counts["chart"] >= 3:
        recommendations.append("evitar gráficos simultâneos lado a lado e renderizar análises secundárias após seleção")
    if counts["tabs"] >= 2:
        recommendations.append("avaliar se abas ocultam conteúdo pesado sem impedir sua execução antecipada")
    if counts["expander"] == 0 and (counts["dataframe"] + counts["chart"] >= 4):
        recommendations.append("introduzir progressão por expansores ou controles explícitos de carregamento")
    if line_count >= 350:
        recommendations.append("dividir a página em seções menores e componentes reutilizáveis")
    if counts["metrics"] if False else False:
        pass
    if not recommendations:
        recommendations.append("manter e validar em celular, tablet e desktop")

    if pressure >= 30 or max_columns >= 5 or counts["dataframe"] >= 6:
        priority = "critical"
    elif pressure >= 18 or max_columns >= 4 or counts["dataframe"] >= 4:
        priority = "high"
    elif pressure >= 9 or max_columns >= 3:
        priority = "medium"
    else:
        priority = "low"

    return PageInventory(
        function=node.name,
        start_line=node.lineno,
        end_line=end_line,
        lines=line_count,
        columns_calls=counts["columns"],
        max_columns=max_columns,
        metrics=counts["metric"],
        dataframes=counts["dataframe"],
        charts=counts["chart"],
        tabs=counts["tabs"],
        expanders=counts["expander"],
        buttons=counts["button"],
        download_buttons=counts["download_button"],
        selectors=counts["selector"],
        horizontal_pressure=pressure,
        priority=priority,
        recommendations=tuple(recommendations),
    )


def run() -> list[PageInventory]:
    source = APP_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(APP_PATH))
    return sorted(
        (analyse_function(node) for node in render_functions(tree)),
        key=lambda item: (-item.horizontal_pressure, item.function),
    )


def markdown_report(items: list[PageInventory]) -> str:
    lines = [
        "# Inventário visual automatizado do Streamlit",
        "",
        "Análise estática das funções de renderização em `app/streamlit_app.py`.",
        "Os números indicam pressão estrutural; a decisão final depende de inspeção visual em execução.",
        "",
        "| Prioridade | Função | Linhas | Chamadas de colunas | Máximo de colunas | Métricas | Tabelas | Gráficos | Abas | Expansores | Pressão horizontal |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in items:
        lines.append(
            f"| {item.priority} | `{item.function}` | {item.lines} | {item.columns_calls} | {item.max_columns} | "
            f"{item.metrics} | {item.dataframes} | {item.charts} | {item.tabs} | {item.expanders} | {item.horizontal_pressure} |"
        )

    lines.extend(["", "## Recomendações por função", ""])
    for item in items:
        lines.append(f"### `{item.function}` — {item.priority}")
        lines.append("")
        for recommendation in item.recommendations:
            lines.append(f"- {recommendation};")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    items = run()
    payload = [asdict(item) for item in items]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    output = ROOT / "docs" / "audit" / "streamlit_visual_inventory_generated.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown_report(items), encoding="utf-8")
    print(f"\nGenerated {output.relative_to(ROOT)} for {len(items)} render functions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
