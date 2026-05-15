import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.european_aggregators import write_european_aggregator_evaluation


def main():
    outputs = write_european_aggregator_evaluation(OUTPUT_DIR)
    evaluation_df = outputs["evaluation"]
    probes_df = outputs["probes"]

    print("Avaliação dos agregadores europeus candidatos atualizada:")
    print(f"- agregadores avaliados: {len(evaluation_df)}")
    print(f"- sondagens executadas: {len(probes_df)}")
    for _, row in evaluation_df.iterrows():
        print(
            f"- {row['label']}: {row['candidate_status']} | "
            f"resultados preliminares={row['search_result_count_total']}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
