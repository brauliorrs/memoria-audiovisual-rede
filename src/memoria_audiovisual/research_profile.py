from collections import Counter

RESEARCH_WORKING_TITLE = "research.profile.title"
RESEARCH_SUBTITLE = "research.profile.subtitle"
RESEARCH_MAIN_QUESTION = "research.profile.main_question"

RESEARCH_PLATFORM_POSITIONING = [
    ("research.positioning.function.label", "research.positioning.function.value"),
    ("research.positioning.uses.label", "research.positioning.uses.value"),
    ("research.positioning.current_scope.label", "research.positioning.current_scope.value"),
    ("research.positioning.maturation.label", "research.positioning.maturation.value"),
]

RESEARCH_PARAMETER_ROWS = [
    ("research.parameter.question", "research.parameter.question.platform", "research.parameter.question.evidence", "adapting"),
    ("research.parameter.infrastructure", "research.parameter.infrastructure.platform", "research.parameter.infrastructure.evidence", "implemented"),
    ("research.parameter.units", "research.parameter.units.platform", "research.parameter.units.evidence", "implemented"),
    ("research.parameter.longitudinal", "research.parameter.longitudinal.platform", "research.parameter.longitudinal.evidence", "implemented"),
    ("research.parameter.visibility", "research.parameter.visibility.platform", "research.parameter.visibility.evidence", "implemented"),
    ("research.parameter.europe", "research.parameter.europe.platform", "research.parameter.europe.evidence", "adapting"),
    ("research.parameter.reproducibility", "research.parameter.reproducibility.platform", "research.parameter.reproducibility.evidence", "implemented"),
    ("research.parameter.indicators", "research.parameter.indicators.platform", "research.parameter.indicators.evidence", "to_develop"),
    ("research.parameter.findability", "research.parameter.findability.platform", "research.parameter.findability.evidence", "adapting"),
    ("research.parameter.ethics", "research.parameter.ethics.platform", "research.parameter.ethics.evidence", "to_develop"),
]

RESEARCH_NEXT_ADJUSTMENT_ROWS = [
    ("1", "research.adjustment.visibility_index", "research.adjustment.visibility_index.result"),
    ("2", "research.adjustment.europe_design", "research.adjustment.europe_design.result"),
    ("3", "research.adjustment.detectability", "research.adjustment.detectability.result"),
    ("4", "research.adjustment.ethics", "research.adjustment.ethics.result"),
    ("5", "research.adjustment.report", "research.adjustment.report.result"),
]

STATUS_KEYS = {
    "implemented": "research.status.implemented",
    "adapting": "research.status.adapting",
    "to_develop": "research.status.to_develop",
}

def build_research_positioning_rows(translator):
    return [
        {translator("research.columns.dimension"): translator(label), translator("research.columns.definition"): translator(value)}
        for label, value in RESEARCH_PLATFORM_POSITIONING
    ]

def build_research_parameter_rows(translator):
    return [
        {
            translator("research.columns.parameter"): translator(parameter),
            translator("research.columns.platform_translation"): translator(platform),
            translator("research.columns.current_evidence"): translator(evidence),
            translator("research.columns.status"): translator(STATUS_KEYS[status]),
        }
        for parameter, platform, evidence, status in RESEARCH_PARAMETER_ROWS
    ]

def build_research_next_adjustment_rows(translator):
    return [
        {
            translator("research.columns.priority"): priority,
            translator("research.columns.adjustment"): translator(adjustment),
            translator("research.columns.expected_result"): translator(result),
        }
        for priority, adjustment, result in RESEARCH_NEXT_ADJUSTMENT_ROWS
    ]

def summarize_research_parameter_status(rows=None):
    source = RESEARCH_PARAMETER_ROWS if rows is None else rows
    if source and isinstance(source[0], tuple):
        return dict(Counter(row[3] for row in source))
    return {}
