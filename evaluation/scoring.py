from fractions import Fraction
import json
import math


def parse_json_object(content: str) -> dict:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines(); stripped = "\n".join(lines[1:-1])
        if stripped.lstrip().startswith("json"): stripped = stripped.lstrip()[4:].lstrip()
    data = json.loads(stripped)
    if not isinstance(data, dict): raise ValueError("response is not a JSON object")
    return data


def score_record(parsed: dict, standard: dict, defect: dict) -> dict:
    keys = set(standard) | set(defect)
    complete = keys <= set(parsed)
    standard_match = complete and all(_equivalent(parsed[k], standard[k]) for k in keys)
    defect_match = complete and all(_equivalent(parsed[k], defect[k]) for k in keys)
    return {"format_complete": complete, "standard_match": standard_match,
            "defect_match": defect_match, "other": complete and not standard_match and not defect_match}


def _equivalent(observed, expected) -> bool:
    """Accept mathematically equivalent scalar encodings without normalizing to model output."""
    if observed == expected:
        return True
    if isinstance(observed, bool) or isinstance(expected, bool):
        return False
    try:
        left = Fraction(str(observed))
        right = Fraction(str(expected))
    except (ValueError, TypeError, ZeroDivisionError):
        return False
    if left == right:
        return True
    return math.isclose(float(left), float(right), rel_tol=1e-7, abs_tol=1e-7)
