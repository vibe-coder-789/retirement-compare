from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .models import (
    ComparisonRequest,
    ComparisonResponse,
    ContributionResponse,
    TaxComparisonResponse,
    TaxResultResponse,
    ProjectionSummaryResponse,
    YearlyProjectionResponse,
    LimitsResponse,
)
from .calculators import ContributionCalculator, TaxCalculator, ProjectionCalculator
from .calculators.tax import get_state_tax_rate
from .calculators.contributions import CONTRIBUTION_LIMITS

app = FastAPI(
    title="Retirement Plan Comparison",
    description="Compare Traditional 401(k) vs Roth 401(k)",
    version="1.0.0",
)

static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def root():
    return FileResponse(static_path / "index.html")


@app.get("/api/limits/{year}", response_model=LimitsResponse)
async def get_limits(year: int):
    if year not in CONTRIBUTION_LIMITS:
        raise HTTPException(status_code=404, detail=f"Year {year} not supported")

    limits = CONTRIBUTION_LIMITS[year]
    return LimitsResponse(
        year=year,
        base_limit=limits["base"],
        catchup_limit=limits["catchup"],
        catchup_age=limits["catchup_age"],
        total_with_catchup=limits["base"] + limits["catchup"],
    )


@app.post("/api/compare", response_model=ComparisonResponse)
async def compare_plans(request: ComparisonRequest):
    if request.retirement_age <= request.current_age:
        raise HTTPException(
            status_code=400, detail="Retirement age must be greater than current age"
        )

    contrib_calc = ContributionCalculator(year=2024)
    contribution = contrib_calc.calculate_contribution(
        annual_income=request.annual_income,
        age=request.current_age,
        contribution_mode=request.contribution_mode,
        contribution_amount=request.contribution_amount,
        employer_match_percent=request.employer_match_percent,
        employer_match_cap_percent=request.employer_match_cap_percent,
    )

    # Create tax calculators for current and retirement (may have different state tax rates)
    current_state_rate = get_state_tax_rate(request.current_state)
    retirement_state_rate = get_state_tax_rate(request.retirement_state)

    current_tax_calc = TaxCalculator(
        filing_status=request.filing_status,
        state_tax_rate=current_state_rate,
    )
    retirement_tax_calc = TaxCalculator(
        filing_status=request.filing_status,
        state_tax_rate=retirement_state_rate,
    )
    total_income = request.annual_income + request.annual_bonus

    # Function to calculate take-home for a given Traditional split
    def get_take_home_for_split(split_percent: float) -> float:
        traditional_contrib = contribution.employee_contribution * (split_percent / 100)
        tax_result = current_tax_calc.calculate_tax(
            total_income - traditional_contrib,
            gross_wages=total_income  # FICA based on gross
        )
        return total_income - contribution.employee_contribution - tax_result.total_tax

    # Calculate current year taxes (using current state rate)
    current_traditional_tax = current_tax_calc.calculate_tax(
        total_income - contribution.employee_contribution,
        gross_wages=total_income  # FICA based on gross wages
    )
    current_roth_tax = current_tax_calc.calculate_tax(total_income, gross_wages=total_income)
    current_year_savings = current_roth_tax.total_tax - current_traditional_tax.total_tax

    # Calculate retirement taxes (using retirement state rate)
    # No FICA on retirement income (401k withdrawals are not wages)
    retirement_tax = retirement_tax_calc.calculate_tax(
        request.expected_retirement_income,
        include_fica=False
    )

    # Calculate take-home for the actual split
    current_split = request.traditional_split
    current_take_home = get_take_home_for_split(current_split)

    # Also calculate 100% Traditional and 100% Roth for comparison
    trad_take_home = get_take_home_for_split(100)
    roth_take_home = get_take_home_for_split(0)

    proj_calc = ProjectionCalculator(
        annual_return=request.expected_return / 100,
        taxable_return=request.taxable_return / 100,
        contribution_timing=request.contribution_timing,
        savings_rate=request.savings_rate / 100,
    )

    # Calculate projections for 100% Traditional and 100% Roth (for comparison)
    # Using split method for consistency (employer match always goes to Traditional)
    trad_100_projection = proj_calc.calculate_split_projection(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        annual_contribution=contribution.employee_contribution,
        employer_match=contribution.employer_match,
        retirement_tax_rate=retirement_tax.effective_rate,
        take_home=trad_take_home,
        initial_401k_balance=request.initial_401k_balance,
        initial_taxable_balance=request.initial_taxable_balance,
        mega_backdoor_contribution=request.mega_backdoor_contribution,
        traditional_split=100,
    )
    roth_100_projection = proj_calc.calculate_split_projection(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        annual_contribution=contribution.employee_contribution,
        employer_match=contribution.employer_match,
        retirement_tax_rate=retirement_tax.effective_rate,
        take_home=roth_take_home,
        initial_401k_balance=request.initial_401k_balance,
        initial_taxable_balance=request.initial_taxable_balance,
        mega_backdoor_contribution=request.mega_backdoor_contribution,
        traditional_split=0,
    )

    # Find optimal split (brute force)
    optimal_split, optimal_after_tax = proj_calc.find_optimal_split(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        annual_contribution=contribution.employee_contribution,
        employer_match=contribution.employer_match,
        retirement_tax_rate=retirement_tax.effective_rate,
        take_home_at_split=get_take_home_for_split,
        initial_401k_balance=request.initial_401k_balance,
        initial_taxable_balance=request.initial_taxable_balance,
        mega_backdoor_contribution=request.mega_backdoor_contribution,
    )

    # Calculate bracket-aware optimal (tax-bracket strategy)
    bracket_optimal_amount, bracket_explanation = current_tax_calc.calculate_optimal_traditional(
        current_income=total_income,
        max_contribution=contribution.employee_contribution,
        retirement_tax_rate=retirement_tax.effective_rate,
    )
    bracket_optimal_split = round(
        (bracket_optimal_amount / contribution.employee_contribution) * 100
    ) if contribution.employee_contribution > 0 else 0

    # Calculate projection for the user's selected split
    split_projection = proj_calc.calculate_split_projection(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        annual_contribution=contribution.employee_contribution,
        employer_match=contribution.employer_match,
        retirement_tax_rate=retirement_tax.effective_rate,
        take_home=current_take_home,
        initial_401k_balance=request.initial_401k_balance,
        initial_taxable_balance=request.initial_taxable_balance,
        mega_backdoor_contribution=request.mega_backdoor_contribution,
        traditional_split=current_split,
    )

    if roth_100_projection.after_tax_total > trad_100_projection.after_tax_total:
        advantage = "Roth 401(k)"
        advantage_amount = roth_100_projection.after_tax_total - trad_100_projection.after_tax_total
    else:
        advantage = "Traditional 401(k)"
        advantage_amount = trad_100_projection.after_tax_total - roth_100_projection.after_tax_total

    return ComparisonResponse(
        contribution=ContributionResponse(
            employee_contribution=contribution.employee_contribution,
            employer_match=contribution.employer_match,
            total_contribution=contribution.total_contribution,
            max_employee_allowed=contribution.max_employee_allowed,
            is_over_limit=contribution.is_over_limit,
        ),
        tax_comparison=TaxComparisonResponse(
            current_traditional=TaxResultResponse(
                taxable_income=current_traditional_tax.taxable_income,
                federal_tax=current_traditional_tax.federal_tax,
                state_tax=current_traditional_tax.state_tax,
                fica_tax=current_traditional_tax.fica_tax,
                total_tax=current_traditional_tax.total_tax,
                effective_rate=current_traditional_tax.effective_rate,
                marginal_rate=current_traditional_tax.marginal_rate,
            ),
            current_roth=TaxResultResponse(
                taxable_income=current_roth_tax.taxable_income,
                federal_tax=current_roth_tax.federal_tax,
                state_tax=current_roth_tax.state_tax,
                fica_tax=current_roth_tax.fica_tax,
                total_tax=current_roth_tax.total_tax,
                effective_rate=current_roth_tax.effective_rate,
                marginal_rate=current_roth_tax.marginal_rate,
            ),
            current_year_tax_savings=current_year_savings,
            retirement_tax_rate=retirement_tax.effective_rate,
            break_even_rate=current_traditional_tax.marginal_rate,  # Break-even is current marginal rate
        ),
        projection_summary=ProjectionSummaryResponse(
            traditional_final_balance=split_projection.traditional_balance,
            roth_final_balance=split_projection.roth_balance,
            traditional_after_tax=trad_100_projection.after_tax_total,
            roth_after_tax=roth_100_projection.after_tax_total,
            traditional_taxable_balance=split_projection.taxable_balance,
            roth_taxable_balance=split_projection.taxable_balance,
            traditional_mega_backdoor_balance=split_projection.mega_backdoor_balance,
            roth_mega_backdoor_balance=split_projection.mega_backdoor_balance,
            actual_mega_backdoor=split_projection.actual_mega_backdoor,
            total_contributions=split_projection.total_contributions,
            total_employer_match=split_projection.total_employer_match,
            total_growth_traditional=trad_100_projection.total_growth,
            total_growth_roth=roth_100_projection.total_growth,
            advantage=advantage,
            advantage_amount=round(advantage_amount, 2),
            optimal_split=optimal_split,
            optimal_after_tax=optimal_after_tax,
            current_split=current_split,
            current_split_after_tax=split_projection.after_tax_total,
            bracket_optimal_split=bracket_optimal_split,
            bracket_explanation=bracket_explanation,
        ),
        traditional_projections=[
            YearlyProjectionResponse(
                year=p.year,
                age=p.age,
                contribution=p.contribution,
                employer_match=p.employer_match,
                growth=p.growth,
                balance=p.balance,
                total_wealth=p.total_wealth,
                after_tax_wealth=p.after_tax_wealth,
            )
            for p in trad_100_projection.projections
        ],
        roth_projections=[
            YearlyProjectionResponse(
                year=p.year,
                age=p.age,
                contribution=p.contribution,
                employer_match=p.employer_match,
                growth=p.growth,
                balance=p.balance,
                total_wealth=p.total_wealth,
                after_tax_wealth=p.after_tax_wealth,
            )
            for p in roth_100_projection.projections
        ],
    )
