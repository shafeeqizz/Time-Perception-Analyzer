import pytest
from types import SimpleNamespace

from app.services.metrics import compute_summary


def make_entry(est, act):
    return SimpleNamespace(
        estimated_min=est,
        actual_min=act,
        difficulty=3,
        mood=3,
        distractions=1
    )


def test_compute_summary_underestimation():
    entries = [
        make_entry(30, 45),  # 50% error
        make_entry(20, 30),  # 50% error
    ]

    result = compute_summary(entries)

    assert result["total_entries"] == 2
    assert result["avg_percent_error"] == 50.0
    assert result["accuracy_score"] == 50.0


def test_compute_summary_empty():
    result = compute_summary([])
    assert result["total_entries"] == 0
    assert result["accuracy_score"] == 100.0
