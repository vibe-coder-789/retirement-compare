import pytest
from app.calculators.tax import TaxCalculator


class TestTaxCalculator:
    def test_single_filer_22_bracket(self):
        calc = TaxCalculator(filing_status="single")
        result = calc.calculate_tax(75000)
        assert result.marginal_rate == 0.22
        assert result.total_tax > 0

    def test_single_filer_effective_rate(self):
        calc = TaxCalculator(filing_status="single")
        result = calc.calculate_tax(100000)
        assert result.effective_rate < result.marginal_rate
        assert 0.15 < result.effective_rate < 0.25

    def test_married_filing_jointly(self):
        calc = TaxCalculator(filing_status="married_filing_jointly")
        result = calc.calculate_tax(80000)
        assert result.marginal_rate == 0.12

    def test_zero_income(self):
        calc = TaxCalculator(filing_status="single")
        result = calc.calculate_tax(0)
        assert result.total_tax == 0
        assert result.effective_rate == 0

    def test_tax_comparison_shows_savings(self):
        calc = TaxCalculator(filing_status="single")
        comparison = calc.compare_tax_impact(
            current_income=100000,
            traditional_contribution=10000,
            retirement_income=60000,
        )
        assert comparison.current_year_tax_savings > 0
        assert comparison.current_traditional.total_tax < comparison.current_roth.total_tax

    def test_high_income_bracket(self):
        calc = TaxCalculator(filing_status="single")
        result = calc.calculate_tax(300000)
        assert result.marginal_rate == 0.35
