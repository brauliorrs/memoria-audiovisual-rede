"""Development verification of VAL-009 metrics; not a freeze/disclosure runner."""


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def gate(criteria):
    if any(value is False for value in criteria):
        return "FAIL"
    if any(value is None for value in criteria):
        return "INCONCLUSIVE"
    return "PASS"


def at_least(value, threshold):
    return None if value is None else value >= threshold


def binary_metrics(counts):
    tp, tn, fp, fn = (counts[key] for key in ("TP", "TN", "FP", "FN"))
    return {**counts, "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
            "specificity": ratio(tn, tn + fp), "f1": ratio(2 * tp, 2 * tp + fp + fn),
            "accuracy": ratio(tp + tn, tp + tn + fp + fn)}


def evaluate_development(expected, humans, predictions, *, protocol):
    """Verify formulas on known/synthetic rows, with exact manifest ID matching.

    Independent evaluation additionally requires a verified sealed run, hashes,
    review provenance and disclosure chronology; this function cannot certify them.
    """
    result = {"sample_role": "development_metrics_verification_only",
              "is_independent_validation_result": False, "m4_scaling_allowed": False}
    labels = protocol["labels"]["surface_types"]
    access_labels = protocol["labels"]["access_states"]
    positives = set(protocol["labels"]["item_positive"])
    try:
        indexed = []
        for rows in (expected, humans, predictions):
            index = {}
            for row in rows:
                identity = row["review_unit_id"]
                if not isinstance(identity, str) or not identity or identity in index:
                    raise ValueError("Empty or duplicate review ID")
                index[identity] = row
            indexed.append(index)
        manifest, human_by_id, predicted_by_id = indexed
        if set(manifest) != set(human_by_id) or set(manifest) != set(predicted_by_id):
            raise ValueError("Missing or extra review/prediction IDs")
        for identity, expected_row in manifest.items():
            human, prediction = human_by_id[identity], predicted_by_id[identity]
            if not isinstance(expected_row["entity_id"], str) or not expected_row["entity_id"]:
                raise ValueError("Missing entity identity")
            for row in (human, prediction):
                if any(row[key] != expected_row[key] for key in ("entity_id", "page_url")):
                    raise ValueError("Entity/URL identity mismatch")
            for row, prefix in ((human, "human"), (prediction, "predicted")):
                surface = row[f"{prefix}_surface_type"]
                if surface not in labels or row[f"{prefix}_access_state"] not in access_labels:
                    raise ValueError("Invalid surface or access label")
                item_key = "human_is_item_level" if prefix == "human" else "predicted_item_level"
                expected_item = None if prefix == "human" and surface == "unknown" else surface in positives
                if row[item_key] is not expected_item:
                    raise ValueError("Incompatible surface/item mapping")
    except (KeyError, TypeError, ValueError) as error:
        return {**result, "decision": "INVALID", "integrity_error": str(error)}

    matrix = [[0] * len(labels) for _ in labels]
    access_matrix = [[0] * len(access_labels) for _ in access_labels]
    counts = dict.fromkeys(("TP", "TN", "FP", "FN"), 0)
    entities, excluded = {}, 0
    for identity, expected_row in manifest.items():
        human, prediction = human_by_id[identity], predicted_by_id[identity]
        h, p = human["human_surface_type"], prediction["predicted_surface_type"]
        matrix[labels.index(h)][labels.index(p)] += 1
        ha, pa = human["human_access_state"], prediction["predicted_access_state"]
        access_matrix[access_labels.index(ha)][access_labels.index(pa)] += 1
        entity = entities.setdefault(expected_row["entity_id"], {
            "units": 0, "exact_correct": 0, "access_correct": 0,
            "TP": 0, "TN": 0, "FP": 0, "FN": 0, "human_unknown_excluded": 0})
        entity["units"] += 1
        entity["exact_correct"] += h == p
        entity["access_correct"] += ha == pa
        if human["human_is_item_level"] is None:
            excluded += 1
            entity["human_unknown_excluded"] += 1
        else:
            key = ("TP" if prediction["predicted_item_level"] else "FN") if human["human_is_item_level"] else ("FP" if prediction["predicted_item_level"] else "TN")
            counts[key] += 1
            entity[key] += 1
    n = len(manifest)
    per_class = {}
    for i, label in enumerate(labels):
        support, predicted, tp = sum(matrix[i]), sum(row[i] for row in matrix), matrix[i][i]
        per_class[label] = {"support": support, "predicted_total": predicted,
                            "human_supported": support > 0,
                            "precision": ratio(tp, predicted) or 0,
                            "recall": ratio(tp, support) or 0,
                            "f1": ratio(2 * tp, support + predicted) or 0}
    supported = [row for row in per_class.values() if row["support"]]
    fine = {"class_order": labels, "confusion_matrix_rows_human_columns_prediction": matrix,
            "per_class": per_class, "accuracy": ratio(sum(matrix[i][i] for i in range(len(labels))), n),
            "weighted_f1": ratio(sum(row["support"] * row["f1"] for row in supported), n),
            "macro_f1_all_classes": sum(row["f1"] for row in per_class.values()) / len(labels),
            "macro_f1_supported_classes": ratio(sum(row["f1"] for row in supported), len(supported))}
    binary = {**binary_metrics(counts), "human_unknown_excluded": excluded}
    access = {"class_order": access_labels, "confusion_matrix_rows_human_columns_prediction": access_matrix,
              "agreement": ratio(sum(access_matrix[i][i] for i in range(len(access_labels))), n), "total": n}
    thresholds = protocol["gates"]
    fine_gate = thresholds["fine_grained"]
    item_gate = thresholds["item_level"]
    major = {label: row["recall"] >= fine_gate["major_class_recall_minimum"]
             for label, row in per_class.items() if row["support"] >= fine_gate["major_class_support_minimum"]}
    entity_rule = {name: row["TP"] >= 1 for name, row in entities.items() if row["TP"] + row["FN"] >= 2}
    for row in entities.values():
        row.update(binary_metrics(row))
        row["exact_accuracy"] = row["exact_correct"] / row["units"]
        row["access_agreement"] = row["access_correct"] / row["units"]
    decisions = {
        "fine_grained": gate([at_least(fine["weighted_f1"], fine_gate["weighted_f1_minimum"]), *major.values()]),
        "item_level": gate([at_least(binary[key], item_gate[f"{key}_minimum"]) for key in ("precision", "recall", "specificity")] + list(entity_rule.values())),
        "access": gate([at_least(access["agreement"], thresholds["access"]["agreement_minimum"])])}
    sufficient = n >= protocol["sampling"]["minimum_review_units"] and len(entities) >= protocol["sampling"]["minimum_entities"]
    decision = "FAIL" if "FAIL" in decisions.values() else "INCONCLUSIVE" if not sufficient or "INCONCLUSIVE" in decisions.values() else "PASS"
    return {**result, "decision": decision, "units_total": n, "sample_sufficient": sufficient,
            "fine": fine, "binary": binary, "access": access, "per_entity": entities,
            "major_class_gate": major, "entity_item_gate": entity_rule, "gates": decisions}
