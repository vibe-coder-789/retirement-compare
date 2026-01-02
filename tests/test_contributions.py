import pytest
from app.calculators.contributions import ContributionCalculator


class TestContributionCalculator:
    def test_basic_contribution_percentage(self):
        calc = ContributionCalculator(year=2024)
        result = calc.calculate_contribution(
            annual_income=100000,
            age=35,
            contribution_mode="percentage",
            contribution_amount=10,
            employer_match_percent=50,
            employer_match_cap_percent=6,
        )
        assert result.employee_contribution == 10000
        assert result.employer_match == 3000
        assert result.total_contribution == 13000

    def test_basic_contribution_dollar(self):
        calc = ContributionCalculator(year=2024)
        result = calc.calculate_contribution(
            annual_income=100000,
            age=35,
            contribution_mode="dollar",
            contribution_amount=15000,
            employer_match_percent=50,
            employer_match_cap_percent=6,
        )
        assert result.employee_contribution == 15000
        assert result.employer_match == 3000
        assert result.total_contribution == 18000

    def test_contribution_limit_enforced(self):
        calc = ContributionCalculator(year=2024)
        result = calc.calculate_contribution(
            annual_income=500000,
            age=35,
            contribution_mode="dollar",
            contribution_amount=50000,
            employer_match_percent=100,
            employer_match_cap_percent=6,
        )
        assert result.employee_contribution == 23000
        assert result.is_over_limit is True

    def test_catchup_contribution(self):
        calc = ContributionCalculator(year=2024)
        max_contribution = calc.get_max_contribution(age=55)
        assert max_contribution == 30500

    def test_no_catchup_under_50(self):
        calc = ContributionCalculator(year=2024)
        max_contribution = calc.get_max_contribution(age=49)
        assert max_contribution == 23000

    def test_employer_match_capped(self):
        calc = ContributionCalculator(year=2024)
        result = calc.calculate_contribution(
            annual_income=100000,
            age=35,
            contribution_mode="percentage",
            contribution_amount=20,
            employer_match_percent=100,
            employer_match_cap_percent=6,
        )
        assert result.employer_match == 6000
