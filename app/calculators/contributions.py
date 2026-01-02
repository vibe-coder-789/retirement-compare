from dataclasses import dataclass
from typing import Literal

CONTRIBUTION_LIMITS = {
    2024: {"base": 23000, "catchup": 7500, "catchup_age": 50},
    2025: {"base": 23500, "catchup": 7500, "catchup_age": 50},
}


@dataclass
class ContributionResult:
    employee_contribution: float
    employer_match: float
    total_contribution: float
    max_employee_allowed: float
    is_over_limit: bool
    contribution_limit_used: int


class ContributionCalculator:
    def __init__(self, year: int = 2024):
        self.year = year
        self.limits = CONTRIBUTION_LIMITS.get(year, CONTRIBUTION_LIMITS[2024])

    def get_max_contribution(self, age: int) -> float:
        base = self.limits["base"]
        if age >= self.limits["catchup_age"]:
            return base + self.limits["catchup"]
        return base

    def calculate_contribution(
        self,
        annual_income: float,
        age: int,
        contribution_mode: Literal["percentage", "dollar"],
        contribution_amount: float,
        employer_match_percent: float,
        employer_match_cap_percent: float,
    ) -> ContributionResult:
        max_allowed = self.get_max_contribution(age)

        if contribution_mode == "percentage":
            employee_contribution = annual_income * (contribution_amount / 100)
        else:
            employee_contribution = contribution_amount

        is_over_limit = employee_contribution > max_allowed
        employee_contribution = min(employee_contribution, max_allowed)

        matchable_salary = annual_income * (employer_match_cap_percent / 100)
        employee_for_match = min(employee_contribution, matchable_salary)
        employer_match = employee_for_match * (employer_match_percent / 100)

        return ContributionResult(
            employee_contribution=round(employee_contribution, 2),
            employer_match=round(employer_match, 2),
            total_contribution=round(employee_contribution + employer_match, 2),
            max_employee_allowed=max_allowed,
            is_over_limit=is_over_limit,
            contribution_limit_used=self.year,
        )
