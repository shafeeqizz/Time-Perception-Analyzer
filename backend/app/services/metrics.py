from __future__ import annotations
from statistics import mean
from collections import defaultdict
from datetime import datetime, timedelta
import math

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_summary(entries) -> dict:
    """
    entries: iterable of objects with estimated_min and actual_min
    Returns % values where appropriate.
    """
    entries = list(entries)
    if not entries:
        return {
            "total_entries": 0,
            "avg_percent_error": 0.0,        # signed (%)
            "avg_abs_percent_error": 0.0,    # magnitude (%)
            "overconfidence_index": 0.0,     # underestimation only (%)
            "accuracy_score": 100.0,         # 0–100
        }

    percent_errors = []
    abs_percent_errors = []

    for e in entries:
        est = max(int(e.estimated_min), 1)
        act = int(e.actual_min)
        pe = (act - est) / est  # signed
        percent_errors.append(pe)
        abs_percent_errors.append(abs(pe))

    avg_pe = mean(percent_errors)
    avg_abs_pe = mean(abs_percent_errors)

    # underestimation only (positive percent error)
    overconfidence = mean([max(0.0, pe) for pe in percent_errors])

    # accuracy: penalize typical magnitude of error, clamp at >=100% error -> 0
    accuracy = 100.0 * (1.0 - _clamp(avg_abs_pe, 0.0, 1.0))

    return {
        "total_entries": len(entries),
        "avg_percent_error": round(avg_pe * 100.0, 2),
        "avg_abs_percent_error": round(avg_abs_pe * 100.0, 2),
        "overconfidence_index": round(overconfidence * 100.0, 2),
        "accuracy_score": round(accuracy, 2),
    }


def compute_trends(entries, days: int = 30):
    cutoff = datetime.utcnow() - timedelta(days=days)

    filtered = [e for e in entries if e.created_at >= cutoff]

    grouped = defaultdict(list)

    for e in filtered:
        day = e.created_at.date().isoformat()
        grouped[day].append(e)

    results = []

    for day, items in grouped.items():
        total_minutes = sum(e.actual_min for e in items)

        percent_errors = [
            (e.actual_min - max(e.estimated_min, 1)) / max(e.estimated_min, 1)
            for e in items
        ]

        avg_percent_error = sum(percent_errors) / len(percent_errors)

        results.append({
            "date": day,
            "total_minutes": total_minutes,
            "avg_percent_error": round(avg_percent_error * 100, 2),
        })

    return sorted(results, key=lambda x: x["date"])


def _pearson_corr(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))

    if den_x == 0 or den_y == 0:
        return 0.0

    return num / (den_x * den_y)


def compute_correlations(entries):
    entries = list(entries)
    if len(entries) < 2:
        return {
            "difficulty_vs_error": 0.0,
            "mood_vs_error": 0.0,
            "distractions_vs_error": 0.0,
        }

    errors = [
        (e.actual_min - max(e.estimated_min, 1)) / max(e.estimated_min, 1)
        for e in entries
    ]

    difficulty = [e.difficulty for e in entries]
    mood = [e.mood for e in entries]
    distractions = [e.distractions for e in entries]

    return {
        "difficulty_vs_error": round(_pearson_corr(difficulty, errors), 3),
        "mood_vs_error": round(_pearson_corr(mood, errors), 3),
        "distractions_vs_error": round(_pearson_corr(distractions, errors), 3),
    }


def generate_recommendations(entries):
    entries = list(entries)
    if len(entries) < 3:
        return ["Add more entries to generate meaningful recommendations."]

    from math import copysign

    errors = [
        (e.actual_min - max(e.estimated_min, 1)) / max(e.estimated_min, 1)
        for e in entries
    ]

    avg_error = sum(errors) / len(errors)

    recommendations = []

    # Overall bias
    if avg_error > 0.15:
        recommendations.append(
            "You consistently underestimate task durations. Consider adding a 20–30% time buffer."
        )
    elif avg_error < -0.15:
        recommendations.append(
            "You tend to overestimate task durations. You may be allocating more time than necessary."
        )

    # Difficulty effect
    difficulty_corr = compute_correlations(entries)["difficulty_vs_error"]
    if difficulty_corr > 0.4:
        recommendations.append(
            "Higher difficulty strongly increases underestimation. Add extra buffer for difficulty ≥ 4."
        )

    # Distraction effect
    distraction_corr = compute_correlations(entries)["distractions_vs_error"]
    if distraction_corr > 0.3:
        recommendations.append(
            "Distractions significantly increase estimation error. Schedule focused sessions."
        )

    if not recommendations:
        recommendations.append(
            "Your time estimation is relatively stable. Continue tracking to refine insights."
        )

    return recommendations