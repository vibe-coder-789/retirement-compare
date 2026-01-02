import pytest
from app.calculators.projections import ProjectionCalculator


class TestProjectionCalculator:
    def test_basic_projection(self):
        calc = ProjectionCalculator(annual_return=0.07, contribution_timing="end")
        result = calc.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        assert len(result.traditional_projections) == 30
        assert len(result.roth_projections) == 30
        assert result.traditional_final_balance > 0
        assert result.roth_final_balance > 0

    def test_projections_grow_over_time(self):
        calc = ProjectionCalculator(annual_return=0.07, contribution_timing="monthly")
        result = calc.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        for i in range(1, len(result.traditional_projections)):
            assert result.traditional_projections[i].balance > result.traditional_projections[i-1].balance

    def test_beginning_of_year_grows_more(self):
        calc_beginning = ProjectionCalculator(annual_return=0.07, contribution_timing="beginning")
        calc_end = ProjectionCalculator(annual_return=0.07, contribution_timing="end")

        result_beginning = calc_beginning.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        result_end = calc_end.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        assert result_beginning.traditional_final_balance > result_end.traditional_final_balance

    def test_both_have_taxable_accounts(self):
        calc = ProjectionCalculator(annual_return=0.07, contribution_timing="monthly", savings_rate=0.20)
        result = calc.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        assert result.traditional_taxable_balance > 0
        assert result.roth_taxable_balance > 0
        assert result.traditional_taxable_balance > result.roth_taxable_balance

    def test_roth_taxable_from_lower_take_home(self):
        calc = ProjectionCalculator(annual_return=0.07, contribution_timing="monthly", savings_rate=0.20)
        result = calc.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        diff = result.traditional_taxable_balance - result.roth_taxable_balance
        assert diff > 0

    def test_total_contributions_calculated(self):
        calc = ProjectionCalculator(annual_return=0.07, contribution_timing="monthly")
        result = calc.calculate_projections(
            current_age=35,
            retirement_age=65,
            annual_contribution=10000,
            employer_match=3000,
            retirement_tax_rate=0.15,
            trad_take_home=75000,
            roth_take_home=73000,
        )
        assert result.total_contributions == 10000 * 30
        assert result.total_employer_match == 3000 * 30
