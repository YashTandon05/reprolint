from __future__ import annotations
from dataclasses import dataclass, field

from reprolint.checks.base import Category, CheckResult

CATEGORY_WEIGHTS: dict[Category, float] = {
    Category.ENVIRONMENT: 30.0,
    Category.STOCHASTICITY: 25.0,
    Category.DATA_INTEGRITY: 25.0,
    Category.CODE_QUALITY: 20.0,
}


@dataclass
class CategoryScore:
    category: Category
    earned: float
    possible: float
    weight: float

    @property
    def fraction(self) -> float:
        return self.earned / self.possible if self.possible else 1.0


@dataclass
class Scorecard:
    categories: list[CategoryScore] = field(default_factory=list)
    total: float = 0.0
    results: list[CheckResult] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.total >= 80:
            return "STRONG — likely reproducible"
        if self.total >= 60:
            return "MODERATE — some reproducibility risk"
        if self.total >= 40:
            return "WEAK — significant reproducibility risk"
        return "LIKELY NOT REPRODUCIBLE"


def score(results: list[CheckResult]) -> Scorecard:
    """Aggregate check results into a weighted scorecard out of 100."""
    totals: dict[Category, list[float]] = {}
    for r in results:
        bucket = totals.setdefault(r.category, [0.0, 0.0])
        bucket[0] += r.score
        bucket[1] += r.max_score

    present_weight = sum(CATEGORY_WEIGHTS[c] for c in totals) or 1.0

    categories: list[CategoryScore] = []
    total = 0.0
    for cat, (earned, possible) in totals.items():
        weight = CATEGORY_WEIGHTS[cat]
        cs = CategoryScore(category=cat, earned=earned, possible=possible, weight=weight)
        normalized_weight = weight / present_weight * 100.0
        total += normalized_weight * cs.fraction
        categories.append(cs)

    order = list(CATEGORY_WEIGHTS.keys())
    categories.sort(key=lambda c: order.index(c.category))

    return Scorecard(categories=categories, total=round(total, 1), results=results)