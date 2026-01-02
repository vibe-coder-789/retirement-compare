from dataclasses import dataclass
from typing import Literal

# State income tax rates (approximate top marginal rates for simplicity)
# States with progressive taxes use approximate effective rate for $100k income
STATE_TAX_RATES = {
    "AL": 0.050,  # Alabama
    "AK": 0.000,  # Alaska - no income tax
    "AZ": 0.025,  # Arizona
    "AR": 0.047,  # Arkansas
    "CA": 0.093,  # California (top rate, progressive)
    "CO": 0.044,  # Colorado (flat)
    "CT": 0.060,  # Connecticut
    "DE": 0.066,  # Delaware
    "FL": 0.000,  # Florida - no income tax
    "GA": 0.055,  # Georgia
    "HI": 0.080,  # Hawaii
    "ID": 0.058,  # Idaho
    "IL": 0.050,  # Illinois (flat)
    "IN": 0.032,  # Indiana (flat)
    "IA": 0.057,  # Iowa
    "KS": 0.057,  # Kansas
    "KY": 0.045,  # Kentucky (flat)
    "LA": 0.043,  # Louisiana
    "ME": 0.072,  # Maine
    "MD": 0.058,  # Maryland
    "MA": 0.050,  # Massachusetts (flat)
    "MI": 0.043,  # Michigan (flat)
    "MN": 0.079,  # Minnesota
    "MS": 0.050,  # Mississippi
    "MO": 0.049,  # Missouri
    "MT": 0.059,  # Montana
    "NE": 0.058,  # Nebraska
    "NV": 0.000,  # Nevada - no income tax
    "NH": 0.000,  # New Hampshire - no income tax (interest/dividends only)
    "NJ": 0.064,  # New Jersey
    "NM": 0.049,  # New Mexico
    "NY": 0.085,  # New York (state + NYC)
    "NC": 0.053,  # North Carolina (flat)
    "ND": 0.025,  # North Dakota
    "OH": 0.040,  # Ohio
    "OK": 0.048,  # Oklahoma
    "OR": 0.099,  # Oregon
    "PA": 0.031,  # Pennsylvania (flat)
    "RI": 0.060,  # Rhode Island
    "SC": 0.065,  # South Carolina
    "SD": 0.000,  # South Dakota - no income tax
    "TN": 0.000,  # Tennessee - no income tax
    "TX": 0.000,  # Texas - no income tax
    "UT": 0.047,  # Utah (flat)
    "VT": 0.076,  # Vermont
    "VA": 0.058,  # Virginia
    "WA": 0.000,  # Washington - no income tax
    "WV": 0.055,  # West Virginia
    "WI": 0.065,  # Wisconsin
    "WY": 0.000,  # Wyoming - no income tax
    "DC": 0.085,  # Washington D.C.
}

def get_state_tax_rate(state_code: str) -> float:
    """Get the state tax rate for a given state code."""
    return STATE_TAX_RATES.get(state_code.upper(), 0.05)  # Default 5% if unknown

# FICA (Social Security + Medicare) limits for 2024
FICA_2024 = {
    "social_security_rate": 0.062,  # 6.2%
    "social_security_wage_base": 168600,  # Max wages subject to SS tax
    "medicare_rate": 0.0145,  # 1.45%
    "additional_medicare_rate": 0.009,  # 0.9% additional
    "additional_medicare_threshold_single": 200000,
    "additional_medicare_threshold_mfj": 250000,
}


def calculate_fica_tax(gross_wages: float, filing_status: str = "single") -> float:
    """Calculate FICA taxes (Social Security + Medicare) on gross wages.

    Note: FICA is calculated on gross wages, NOT reduced by 401(k) contributions.
    """
    # Social Security: 6.2% up to wage base
    ss_wages = min(gross_wages, FICA_2024["social_security_wage_base"])
    social_security_tax = ss_wages * FICA_2024["social_security_rate"]

    # Medicare: 1.45% on all wages
    medicare_tax = gross_wages * FICA_2024["medicare_rate"]

    # Additional Medicare: 0.9% on wages over threshold
    threshold = (FICA_2024["additional_medicare_threshold_mfj"]
                 if filing_status == "married_filing_jointly"
                 else FICA_2024["additional_medicare_threshold_single"])
    if gross_wages > threshold:
        medicare_tax += (gross_wages - threshold) * FICA_2024["additional_medicare_rate"]

    return round(social_security_tax + medicare_tax, 2)


TAX_BRACKETS_2024 = {
    "single": [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float("inf"), 0.37),
    ],
    "married_filing_jointly": [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float("inf"), 0.37),
    ],
}


@dataclass
class TaxResult:
    taxable_income: float
    federal_tax: float
    state_tax: float
    fica_tax: float
    total_tax: float  # federal + state + fica
    effective_rate: float
    marginal_rate: float


@dataclass
class TaxComparisonResult:
    current_traditional: TaxResult
    current_roth: TaxResult
    current_year_tax_savings: float
    retirement_traditional: TaxResult
    retirement_roth: TaxResult
    break_even_rate: float


class TaxCalculator:
    def __init__(
        self,
        filing_status: Literal["single", "married_filing_jointly"] = "single",
        year: int = 2024,
        state_tax_rate: float = 0.0,  # State tax rate as decimal (e.g., 0.05 for 5%)
    ):
        self.filing_status = filing_status
        self.brackets = TAX_BRACKETS_2024[filing_status]
        self.state_tax_rate = state_tax_rate

    def calculate_tax(self, taxable_income: float, gross_wages: float = None) -> TaxResult:
        """Calculate taxes on income.

        Args:
            taxable_income: Income after 401(k) deductions (for federal/state tax)
            gross_wages: Original gross wages for FICA calculation (if None, uses taxable_income)
        """
        if gross_wages is None:
            gross_wages = taxable_income

        if taxable_income <= 0:
            fica_tax = calculate_fica_tax(gross_wages, self.filing_status) if gross_wages > 0 else 0
            return TaxResult(
                taxable_income=0, federal_tax=0, state_tax=0, fica_tax=fica_tax,
                total_tax=fica_tax, effective_rate=0, marginal_rate=0.10
            )

        federal_tax = 0
        previous_bracket = 0
        marginal_rate = 0.10

        for bracket_max, rate in self.brackets:
            if taxable_income <= bracket_max:
                federal_tax += (taxable_income - previous_bracket) * rate
                marginal_rate = rate
                break
            else:
                federal_tax += (bracket_max - previous_bracket) * rate
                previous_bracket = bracket_max
                marginal_rate = rate

        # State tax (simplified flat rate)
        state_tax = taxable_income * self.state_tax_rate

        # FICA tax (on gross wages, not reduced by 401k)
        fica_tax = calculate_fica_tax(gross_wages, self.filing_status)

        total_tax = federal_tax + state_tax + fica_tax

        effective_rate = total_tax / gross_wages if gross_wages > 0 else 0

        return TaxResult(
            taxable_income=round(taxable_income, 2),
            federal_tax=round(federal_tax, 2),
            state_tax=round(state_tax, 2),
            fica_tax=round(fica_tax, 2),
            total_tax=round(total_tax, 2),
            effective_rate=round(effective_rate, 4),
            marginal_rate=marginal_rate + self.state_tax_rate,  # Combined marginal rate (excludes FICA)
        )

    def compare_tax_impact(
        self,
        current_income: float,
        traditional_contribution: float,
        retirement_income: float,
    ) -> TaxComparisonResult:
        traditional_taxable = current_income - traditional_contribution
        current_traditional = self.calculate_tax(traditional_taxable)
        current_roth = self.calculate_tax(current_income)

        current_year_savings = current_roth.total_tax - current_traditional.total_tax

        retirement_traditional = self.calculate_tax(retirement_income)
        retirement_roth = self.calculate_tax(retirement_income)

        if traditional_contribution > 0:
            break_even = current_traditional.marginal_rate
        else:
            break_even = 0

        return TaxComparisonResult(
            current_traditional=current_traditional,
            current_roth=current_roth,
            current_year_tax_savings=round(current_year_savings, 2),
            retirement_traditional=retirement_traditional,
            retirement_roth=retirement_roth,
            break_even_rate=break_even,
        )

    def calculate_optimal_traditional(
        self,
        current_income: float,
        max_contribution: float,
        retirement_tax_rate: float,
    ) -> tuple[float, str]:
        """
        Calculate the optimal Traditional 401(k) contribution based on tax brackets.

        Strategy: Use Traditional for income taxed at rates HIGHER than retirement rate.
        Switch to Roth once you'd be reducing income taxed at or below retirement rate.

        Returns: (optimal_traditional_amount, explanation)
        """
        # Use taxable income (after standard deduction) for bracket comparison
        # Standard deduction 2024: $14,600 single, $29,200 MFJ
        std_deduction = 29200 if self.filing_status == "married_filing_jointly" else 14600
        taxable_income = max(0, current_income - std_deduction)

        # Find which bracket boundary we should target
        # We want Traditional to reduce income down to where marginal rate <= retirement rate
        target_taxable = taxable_income
        current_marginal = self.calculate_tax(taxable_income).marginal_rate

        previous_bracket = 0
        for bracket_max, rate in self.brackets:
            if rate <= retirement_tax_rate:
                # This bracket's rate is at or below retirement rate
                # Don't use Traditional to reduce income in this bracket
                if taxable_income > bracket_max:
                    previous_bracket = bracket_max
                    continue
                else:
                    # Current income is in a bracket at/below retirement rate
                    # Don't use Traditional at all for this income
                    target_taxable = taxable_income  # No reduction needed
                    break
            else:
                # This bracket's rate is higher than retirement rate
                # We SHOULD use Traditional for income in this bracket
                if taxable_income <= bracket_max:
                    # We're in this bracket - target the bottom of it
                    target_taxable = previous_bracket
                    break
                else:
                    previous_bracket = bracket_max

        # Calculate how much Traditional contribution needed
        optimal_traditional = taxable_income - target_taxable
        optimal_traditional = max(0, min(optimal_traditional, max_contribution))

        if optimal_traditional >= max_contribution:
            explanation = f"Use 100% Traditional: All your contribution reduces income taxed at {current_marginal*100:.0f}% (> {retirement_tax_rate*100:.1f}% retirement rate)"
        elif optimal_traditional <= 0:
            explanation = f"Use 100% Roth: Your marginal rate ({current_marginal*100:.0f}%) ≤ retirement rate ({retirement_tax_rate*100:.1f}%)"
        else:
            pct = (optimal_traditional / max_contribution) * 100
            explanation = f"Use {pct:.0f}% Traditional (${optimal_traditional:,.0f}) to reduce {current_marginal*100:.0f}% bracket income, rest as Roth"

        return optimal_traditional, explanation
