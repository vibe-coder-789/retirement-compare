from pydantic import BaseModel, Field
from typing import Literal


class ComparisonRequest(BaseModel):
    current_age: int = Field(default=35, ge=18, le=70)
    retirement_age: int = Field(default=65, ge=50, le=80)
    annual_income: float = Field(default=100000, ge=0)
    annual_bonus: float = Field(default=0, ge=0)
    initial_401k_balance: float = Field(default=0, ge=0)
    initial_taxable_balance: float = Field(default=0, ge=0)
    contribution_mode: Literal["percentage", "dollar"] = "percentage"
    contribution_amount: float = Field(default=10, ge=0)
    contribution_timing: Literal["beginning", "end", "monthly"] = "monthly"
    mega_backdoor_contribution: float = Field(default=0, ge=0)
    traditional_split: float = Field(default=100, ge=0, le=100)  # % going to Traditional
    employer_match_percent: float = Field(default=50, ge=0, le=100)
    employer_match_cap_percent: float = Field(default=6, ge=0, le=100)
    expected_retirement_income: float = Field(default=60000, ge=0)
    expected_return: float = Field(default=7, ge=0)
    taxable_return: float = Field(default=6, ge=0)
    filing_status: Literal["single", "married_filing_jointly"] = "single"
    savings_rate: float = Field(default=20, ge=0, le=100)
    current_state: str = Field(default="CA")  # Current state code
    retirement_state: str = Field(default="CA")  # Retirement state code


class TaxResultResponse(BaseModel):
    taxable_income: float
    federal_tax: float
    state_tax: float
    fica_tax: float
    total_tax: float
    effective_rate: float
    marginal_rate: float


class ContributionResponse(BaseModel):
    employee_contribution: float
    employer_match: float
    total_contribution: float
    max_employee_allowed: float
    is_over_limit: bool


class TaxComparisonResponse(BaseModel):
    current_traditional: TaxResultResponse
    current_roth: TaxResultResponse
    current_year_tax_savings: float
    retirement_tax_rate: float
    break_even_rate: float


class YearlyProjectionResponse(BaseModel):
    year: int
    age: int
    contribution: float
    employer_match: float
    growth: float
    balance: float
    total_wealth: float = 0
    after_tax_wealth: float = 0


class ProjectionSummaryResponse(BaseModel):
    traditional_final_balance: float
    roth_final_balance: float
    traditional_after_tax: float
    roth_after_tax: float
    traditional_taxable_balance: float
    roth_taxable_balance: float
    traditional_mega_backdoor_balance: float
    roth_mega_backdoor_balance: float
    actual_mega_backdoor: float  # Capped at take_home
    total_contributions: float
    total_employer_match: float
    total_growth_traditional: float
    total_growth_roth: float
    advantage: str
    advantage_amount: float
    optimal_split: float  # Optimal % for Traditional
    optimal_after_tax: float  # After-tax value at optimal split
    current_split: float  # Current split being used
    current_split_after_tax: float  # After-tax value at current split
    bracket_optimal_split: float  # Bracket-aware optimal split
    bracket_explanation: str  # Explanation of bracket strategy


class ComparisonResponse(BaseModel):
    contribution: ContributionResponse
    tax_comparison: TaxComparisonResponse
    projection_summary: ProjectionSummaryResponse
    traditional_projections: list[YearlyProjectionResponse]
    roth_projections: list[YearlyProjectionResponse]


class LimitsResponse(BaseModel):
    year: int
    base_limit: float
    catchup_limit: float
    catchup_age: int
    total_with_catchup: float
