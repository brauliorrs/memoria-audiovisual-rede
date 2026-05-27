import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.europe_research import (
    EUROPE_RESEARCH_QUEUE_FILENAME,
    EUROPE_RESEARCH_REGISTRY_FILENAME,
    EUROPE_RESEARCH_SUMMARY_FILENAME,
    write_europe_research_outputs,
)


def main():
    outputs = write_europe_research_outputs(OUTPUT_DIR)
    print("Fila de pesquisa europeia atualizada:")
    print(f"- unidades registradas: {len(outputs['registry'])}")
    print(f"- unidades na fila: {len(outputs['queue'])}")
    print(f"- decisões sumarizadas: {len(outputs['summary'])}")
    print(f"- registro: {EUROPE_RESEARCH_REGISTRY_FILENAME}")
    print(f"- fila: {EUROPE_RESEARCH_QUEUE_FILENAME}")
    print(f"- resumo: {EUROPE_RESEARCH_SUMMARY_FILENAME}")
    if not outputs["queue"].empty:
        print("- próximos itens:")
        for _, row in outputs["queue"].head(8).iterrows():
            print(
                f"  - #{row['definitive_queue_rank']} | prioridade {row['queue_priority']} | "
                f"{row['unit_code']} | {row['queue_layer']} | {row['queue_decision']}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
