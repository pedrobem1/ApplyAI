CLASSIFICATION_POINTS = {
    "MATCH": 1.0,
    "PARTIAL": 0.5,
    "NO_MATCH": 0.0,
}

IMPORTANCE_WEIGHTS = {
    "required": 1.5,
    "preferred": 1.0,
    "nice_to_have": 0.5,
    "unknown": 1.0,
}


def calculate_match_score(matches: list[dict[str, str]]) -> float:
    if not matches:
        return 0.0

    obtained = 0.0
    possible = 0.0

    for match in matches:
        weight = IMPORTANCE_WEIGHTS.get(match.get("importance", "unknown"), 1.0)
        points = CLASSIFICATION_POINTS.get(match.get("classification", "NO_MATCH"), 0.0)
        obtained += points * weight
        possible += weight

    if possible == 0:
        return 0.0

    return round((obtained / possible) * 100, 2)

