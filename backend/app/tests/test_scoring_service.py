from app.services.scoring_service import calculate_match_score


def test_calculate_match_score_weights_required_requirements_more_heavily() -> None:
    score = calculate_match_score(
        [
            {"classification": "MATCH", "importance": "required"},
            {"classification": "NO_MATCH", "importance": "preferred"},
        ]
    )

    assert score == 60.0


def test_calculate_match_score_handles_empty_matches() -> None:
    assert calculate_match_score([]) == 0.0

