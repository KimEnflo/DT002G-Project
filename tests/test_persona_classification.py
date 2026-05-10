import json
from pathlib import Path

from scipy.stats import pearsonr
import spacy
import persona_parser

nlp = spacy.load("en_core_web_lg")
ALL_PERSONAS = {
    "question asker",
    "solution provider",
    "technical explainer",
    "critic",
    "none"
}

def compute_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Compute F1 score.
    :param tp: True positive
    :param fp: False positive
    :param fn: False negative
    :return: Tuple with (precision,recall, F1 score)"""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * ((precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

def load_polarities(folder)->dict:
    """Load the polarity data for person test
    :param folder: Path to folder containing polarities
    :return polarities: Dictionary of polarities"""
    polarities = {}
    for file in sorted(Path(folder).glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for category in data.values():
            for sentiment_group in category.values():
                for entry in sentiment_group:
                    uid = entry["user"] + "|" + entry["comment"]

                    polarities[uid] = entry["polarity"]

    return polarities


def print_persona_summary(
        path:Path,
        persona_order:list,
        global_counts:dict,
        global_correct:int,
        global_total:int
):
    """print persona summaries for all threads by writing out the confusion matrix
    :param path:
    :param persona_order: the list of personas in order
    :param global_counts: Global counts
    :param global_correct: Global correct
    :param global_total: Global total"""

    global_acc = (
        global_correct / global_total
        if global_total else 0
    )

    print(f"\nGlobal summary for {path} — all threads")
    print(
        f"Overall accuracy: "
        f"{global_acc:.2%} "
        f"({global_correct}/{global_total})"
    )

    print(
        f"{'Persona':<25} "
        f"{'TP':>4} "
        f"{'FP':>4} "
        f"{'FN':>4} "
        f"{'Prec':>7} "
        f"{'Rec':>7} "
        f"{'F1':>7}"
    )

    all_f1 = []

    for persona in persona_order:
        counts = global_counts[persona]

        p, r, f1 = compute_f1(
            counts["tp"],
            counts["fp"],
            counts["fn"]
        )

        all_f1.append(f1)

        print(
            f"{persona:<25} "
            f"{counts['tp']:>4} "
            f"{counts['fp']:>4} "
            f"{counts['fn']:>4} "
            f"{p:>7.3f} "
            f"{r:>7.3f} "
            f"{f1:>7.3f}"
        )

    macro_f1 = (
        sum(all_f1) / len(all_f1)
        if all_f1 else 0
    )

    persona_f1_no_none = [
        compute_f1(
            global_counts[p]["tp"],
            global_counts[p]["fp"],
            global_counts[p]["fn"]
        )[2]
        for p in ALL_PERSONAS
        if p != "none"
    ]

    macro_f1_no_none = (
        sum(persona_f1_no_none) / len(persona_f1_no_none)
        if persona_f1_no_none else 0
    )

    print(f"\nMacro F1 (all classes): {macro_f1:.3f}")
    print(f"Macro F1 (excl. none):  {macro_f1_no_none:.3f}")

class TestPersonaClassification:

    def test_person(self):
        """Test person scores for context vs non-context sentiment score"""
        context_dir = "../resources/matched_personas/rule-based/context"
        no_context_dir = "../resources/matched_personas/rule-based/no-context"

        context_scores = load_polarities(context_dir)
        no_context_scores = load_polarities(no_context_dir)
        shared = set(context_scores) & set(no_context_scores)
        x = [context_scores[i] for i in shared]
        y = [no_context_scores[i] for i in shared]
        corr, _ = pearsonr(x, y)

        print("Pearson correlation:", corr)


    def test_persona_classification_all(self):
        """Compute F1 scoring."""

        manual_annotations_dir = Path("../resources/manually_annotated_personas")
        matched_persona_dir = Path("../resources/matched_personas")

        matched_persona_data_sets = [
            matched_persona_dir / f"rule-based/context/",
            matched_persona_dir / f"rule-based/no-context/",
            matched_persona_dir / f"AI/context/",
            matched_persona_dir / f"AI/no-context/"
        ]

        persona_order = sorted(ALL_PERSONAS)
        annotation_files = list(manual_annotations_dir.glob("*.json"))

        if not annotation_files:
            print(f"No annotation files found in {manual_annotations_dir}")
            return

        for path in matched_persona_data_sets:
            global_counts = {
                p: {"tp": 0, "fp": 0, "fn": 0}
                for p in ALL_PERSONAS
            }
            global_total = 0
            global_correct = 0

            for annotation_path in annotation_files:

                title = annotation_path.stem
                matched_path = (
                        path / f"matched_personas_{title}.json"
                )
                if not matched_path.exists():
                    continue

                manual_data = persona_parser.load_file(annotation_path)
                model_data = persona_parser.load_file(matched_path)

                model_lookup = {}

                for persona, sentiment_groups in model_data.items():
                    for sentiment, items in sentiment_groups.items():
                        for item in items:
                            model_lookup[item["message_id"]] = (
                                persona.lower().strip()
                            )

                for cid, data in manual_data.items():

                    true_persona = data["persona"].lower().strip()
                    pred_persona = model_lookup.get(cid, "none")

                    global_total += 1

                    if true_persona == pred_persona:
                        global_correct += 1

                    for persona in persona_order:

                        is_true = (true_persona == persona)
                        is_pred = (pred_persona == persona)

                        if is_true and is_pred:
                            global_counts[persona]["tp"] += 1

                        elif not is_true and is_pred:
                            global_counts[persona]["fp"] += 1

                        elif is_true and not is_pred:
                            global_counts[persona]["fn"] += 1

            print_persona_summary(
                path.relative_to(matched_persona_dir),
                persona_order,
                global_counts,
                global_correct,
                global_total
            )