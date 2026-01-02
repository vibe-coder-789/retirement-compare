from dataclasses import dataclass
from typing import Literal


@dataclass
class YearlyProjection:
    year: int
    age: int
    contribution: float
    employer_match: float
    growth: float
    balance: float
    taxable_balance: float = 0
    total_wealth: float = 0
    after_tax_wealth: float = 0
    traditional_balance: float = 0
    roth_balance: float = 0


@dataclass
class SplitProjectionResult:
    """Result for a specific Traditional/Roth split"""
    projections: list[YearlyProjection]
    traditional_balance: float
    roth_balance: float
    taxable_balance: float
    mega_backdoor_balance: float
    after_tax_total: float
    total_contributions: float
    total_employer_match: float
    total_growth: float
    split_percent: float  # % Traditional
    actual_mega_backdoor: float  # Capped at take_home


@dataclass
class ProjectionResult:
    traditional_projections: list[YearlyProjection]
    roth_projections: list[YearlyProjection]
    traditional_final_balance: float
    roth_final_balance: float
    traditional_after_tax: float
    roth_after_tax: float
    traditional_taxable_balance: float
    roth_taxable_balance: float
    traditional_mega_backdoor_balance: float
    roth_mega_backdoor_balance: float
    total_contributions: float
    total_employer_match: float
    total_growth_traditional: float
    total_growth_roth: float


class ProjectionCalculator:
    def __init__(
        self,
        annual_return: float = 0.07,
        taxable_return: float = 0.06,
        contribution_timing: Literal["beginning", "end", "monthly"] = "monthly",
        capital_gains_rate: float = 0.15,
        savings_rate: float = 0.20,
        dividend_yield: float = 0.015,
    ):
        self.annual_return = annual_return
        self.taxable_return = taxable_return
        self.contribution_timing = contribution_timing
        self.capital_gains_rate = capital_gains_rate
        self.savings_rate = savings_rate
        self.dividend_yield = dividend_yield

    def _calculate_year_growth(
        self, starting_balance: float, contribution: float, return_rate: float = None
    ) -> tuple[float, float]:
        r = return_rate if return_rate is not None else self.annual_return

        if self.contribution_timing == "beginning":
            total = starting_balance + contribution
            ending = total * (1 + r)
            growth = ending - starting_balance - contribution
        elif self.contribution_timing == "end":
            ending = starting_balance * (1 + r) + contribution
            growth = starting_balance * r
        else:
            balance_growth = starting_balance * (1 + r)
            monthly_contribution = contribution / 12
            monthly_rate = (1 + r) ** (1 / 12) - 1
            contribution_fv = 0
            for month in range(12):
                months_to_grow = 12 - month - 1
                contribution_fv += monthly_contribution * (
                    (1 + monthly_rate) ** months_to_grow
                )
            ending = balance_growth + contribution_fv
            growth = ending - starting_balance - contribution

        return round(ending, 2), round(growth, 2)

    def _apply_dividend_tax(self, balance: float) -> float:
        return balance * self.dividend_yield * self.capital_gains_rate

    def calculate_projections(
        self,
        current_age: int,
        retirement_age: int,
        annual_contribution: float,
        employer_match: float,
        retirement_tax_rate: float,
        trad_take_home: float,
        roth_take_home: float,
        initial_401k_balance: float = 0,
        initial_taxable_balance: float = 0,
        mega_backdoor_contribution: float = 0,
    ) -> ProjectionResult:
        years = retirement_age - current_age

        traditional_projections = []
        roth_projections = []

        trad_401k_balance = initial_401k_balance
        roth_401k_balance = initial_401k_balance
        trad_taxable_balance = initial_taxable_balance
        roth_taxable_balance = initial_taxable_balance
        trad_taxable_contributions = initial_taxable_balance
        roth_taxable_contributions = initial_taxable_balance
        trad_mega_backdoor_balance = 0.0
        roth_mega_backdoor_balance = 0.0
        total_contributions = 0.0
        total_employer_match = 0.0
        total_growth_trad = 0.0
        total_growth_roth = 0.0

        # Cap mega backdoor at take_home
        trad_mega_backdoor = min(mega_backdoor_contribution, trad_take_home)
        roth_mega_backdoor = min(mega_backdoor_contribution, roth_take_home)

        # Calculate savings: savings_rate applied to spending money (after mega backdoor)
        trad_spending_money = trad_take_home - trad_mega_backdoor
        roth_spending_money = roth_take_home - roth_mega_backdoor

        trad_annual_savings = max(0, trad_spending_money * self.savings_rate)
        roth_annual_savings = max(0, roth_spending_money * self.savings_rate)

        for i in range(years):
            year = i + 1
            age = current_age + year

            total_trad_contrib = annual_contribution + employer_match

            trad_401k_balance, trad_growth = self._calculate_year_growth(
                trad_401k_balance, total_trad_contrib
            )
            roth_401k_balance, roth_growth = self._calculate_year_growth(
                roth_401k_balance, total_trad_contrib
            )

            # Mega backdoor grows tax-free (same rate as 401k), capped at take_home
            trad_mega_backdoor_balance, _ = self._calculate_year_growth(
                trad_mega_backdoor_balance, trad_mega_backdoor
            )
            roth_mega_backdoor_balance, _ = self._calculate_year_growth(
                roth_mega_backdoor_balance, roth_mega_backdoor
            )

            trad_div_tax = self._apply_dividend_tax(trad_taxable_balance)
            trad_taxable_balance, _ = self._calculate_year_growth(
                trad_taxable_balance, trad_annual_savings, self.taxable_return
            )
            trad_taxable_balance -= trad_div_tax
            trad_taxable_contributions += trad_annual_savings

            roth_div_tax = self._apply_dividend_tax(roth_taxable_balance)
            roth_taxable_balance, _ = self._calculate_year_growth(
                roth_taxable_balance, roth_annual_savings, self.taxable_return
            )
            roth_taxable_balance -= roth_div_tax
            roth_taxable_contributions += roth_annual_savings

            trad_total_wealth = trad_401k_balance + trad_taxable_balance + trad_mega_backdoor_balance
            roth_total_wealth = roth_401k_balance + roth_taxable_balance + roth_mega_backdoor_balance

            traditional_projections.append(
                YearlyProjection(
                    year=year,
                    age=age,
                    contribution=annual_contribution,
                    employer_match=employer_match,
                    growth=trad_growth,
                    balance=trad_401k_balance,
                    taxable_balance=round(trad_taxable_balance, 2),
                    total_wealth=round(trad_total_wealth, 2),
                )
            )

            roth_projections.append(
                YearlyProjection(
                    year=year,
                    age=age,
                    contribution=annual_contribution,
                    employer_match=employer_match,
                    growth=roth_growth,
                    balance=roth_401k_balance,
                    taxable_balance=round(roth_taxable_balance, 2),
                    total_wealth=round(roth_total_wealth, 2),
                )
            )

            total_contributions += annual_contribution
            total_employer_match += employer_match
            total_growth_trad += trad_growth
            total_growth_roth += roth_growth

        trad_401k_after_tax = trad_401k_balance * (1 - retirement_tax_rate)
        trad_taxable_gains = trad_taxable_balance - trad_taxable_contributions
        trad_taxable_after_tax = trad_taxable_balance - (trad_taxable_gains * self.capital_gains_rate)
        # Mega backdoor is tax-free at withdrawal (like Roth)
        trad_total_after_tax = trad_401k_after_tax + trad_taxable_after_tax + trad_mega_backdoor_balance

        roth_taxable_gains = roth_taxable_balance - roth_taxable_contributions
        roth_taxable_after_tax = roth_taxable_balance - (roth_taxable_gains * self.capital_gains_rate)
        # Mega backdoor is tax-free at withdrawal
        roth_total_after_tax = roth_401k_balance + roth_taxable_after_tax + roth_mega_backdoor_balance

        return ProjectionResult(
            traditional_projections=traditional_projections,
            roth_projections=roth_projections,
            traditional_final_balance=round(trad_401k_balance, 2),
            roth_final_balance=round(roth_401k_balance, 2),
            traditional_after_tax=round(trad_total_after_tax, 2),
            roth_after_tax=round(roth_total_after_tax, 2),
            traditional_taxable_balance=round(trad_taxable_balance, 2),
            roth_taxable_balance=round(roth_taxable_balance, 2),
            traditional_mega_backdoor_balance=round(trad_mega_backdoor_balance, 2),
            roth_mega_backdoor_balance=round(roth_mega_backdoor_balance, 2),
            total_contributions=round(total_contributions, 2),
            total_employer_match=round(total_employer_match, 2),
            total_growth_traditional=round(total_growth_trad, 2),
            total_growth_roth=round(total_growth_roth, 2),
        )

    def calculate_split_projection(
        self,
        current_age: int,
        retirement_age: int,
        annual_contribution: float,
        employer_match: float,
        retirement_tax_rate: float,
        take_home: float,
        initial_401k_balance: float = 0,
        initial_taxable_balance: float = 0,
        mega_backdoor_contribution: float = 0,
        traditional_split: float = 50,  # % going to Traditional
    ) -> SplitProjectionResult:
        """Calculate projection for a specific Traditional/Roth split."""
        years = retirement_age - current_age
        split_ratio = traditional_split / 100

        projections = []

        # Split the contribution between Traditional and Roth
        traditional_contrib = annual_contribution * split_ratio
        roth_contrib = annual_contribution * (1 - split_ratio)

        # Initial balances (split existing balance proportionally)
        traditional_balance = initial_401k_balance * split_ratio
        roth_balance = initial_401k_balance * (1 - split_ratio)
        taxable_balance = initial_taxable_balance
        taxable_contributions = initial_taxable_balance
        mega_backdoor_balance = 0.0

        total_contributions = 0.0
        total_employer_match_sum = 0.0
        total_growth = 0.0

        # Cap mega backdoor at take_home
        actual_mega_backdoor = min(mega_backdoor_contribution, take_home)

        # Calculate taxable savings: savings_rate applied to spending money (after mega backdoor)
        spending_money = take_home - actual_mega_backdoor
        annual_taxable_savings = max(0, spending_money * self.savings_rate)

        for i in range(years):
            year = i + 1
            age = current_age + year

            # Both Traditional and Roth get employer match (always Traditional)
            total_401k_contrib = annual_contribution + employer_match

            # Grow Traditional balance
            old_trad = traditional_balance
            traditional_balance, trad_growth = self._calculate_year_growth(
                traditional_balance, traditional_contrib + employer_match
            )

            # Grow Roth balance
            old_roth = roth_balance
            roth_balance, roth_growth = self._calculate_year_growth(
                roth_balance, roth_contrib
            )

            combined_growth = trad_growth + roth_growth

            # Mega backdoor grows tax-free (capped at take_home)
            mega_backdoor_balance, _ = self._calculate_year_growth(
                mega_backdoor_balance, actual_mega_backdoor
            )

            # Taxable account with dividend drag
            div_tax = self._apply_dividend_tax(taxable_balance)
            taxable_balance, _ = self._calculate_year_growth(
                taxable_balance, annual_taxable_savings, self.taxable_return
            )
            taxable_balance -= div_tax
            taxable_contributions += annual_taxable_savings

            total_balance = traditional_balance + roth_balance
            total_wealth = total_balance + taxable_balance + mega_backdoor_balance

            # Calculate after-tax wealth for this year
            trad_after_tax = traditional_balance * (1 - retirement_tax_rate)
            roth_after_tax = roth_balance  # Tax-free
            taxable_gains = taxable_balance - taxable_contributions
            taxable_after_tax = taxable_balance - (taxable_gains * self.capital_gains_rate)
            mega_after_tax = mega_backdoor_balance  # Tax-free
            after_tax_wealth = trad_after_tax + roth_after_tax + taxable_after_tax + mega_after_tax

            projections.append(
                YearlyProjection(
                    year=year,
                    age=age,
                    contribution=annual_contribution,
                    employer_match=employer_match,
                    growth=combined_growth,
                    balance=round(total_balance, 2),
                    taxable_balance=round(taxable_balance, 2),
                    total_wealth=round(total_wealth, 2),
                    after_tax_wealth=round(after_tax_wealth, 2),
                    traditional_balance=round(traditional_balance, 2),
                    roth_balance=round(roth_balance, 2),
                )
            )

            total_contributions += annual_contribution
            total_employer_match_sum += employer_match
            total_growth += combined_growth

        # Calculate after-tax values
        # Traditional portion is taxed at retirement rate
        traditional_after_tax = traditional_balance * (1 - retirement_tax_rate)
        # Roth portion is tax-free
        roth_after_tax = roth_balance
        # Taxable: only gains are taxed
        taxable_gains = taxable_balance - taxable_contributions
        taxable_after_tax = taxable_balance - (taxable_gains * self.capital_gains_rate)
        # Mega backdoor is tax-free
        total_after_tax = traditional_after_tax + roth_after_tax + taxable_after_tax + mega_backdoor_balance

        return SplitProjectionResult(
            projections=projections,
            traditional_balance=round(traditional_balance, 2),
            roth_balance=round(roth_balance, 2),
            taxable_balance=round(taxable_balance, 2),
            mega_backdoor_balance=round(mega_backdoor_balance, 2),
            after_tax_total=round(total_after_tax, 2),
            total_contributions=round(total_contributions, 2),
            total_employer_match=round(total_employer_match_sum, 2),
            total_growth=round(total_growth, 2),
            split_percent=traditional_split,
            actual_mega_backdoor=round(actual_mega_backdoor, 2),
        )

    def find_optimal_split(
        self,
        current_age: int,
        retirement_age: int,
        annual_contribution: float,
        employer_match: float,
        retirement_tax_rate: float,
        take_home_at_split: callable,  # Function that returns take-home for a given split
        initial_401k_balance: float = 0,
        initial_taxable_balance: float = 0,
        mega_backdoor_contribution: float = 0,
    ) -> tuple[float, float]:
        """Find the optimal Traditional/Roth split that maximizes after-tax value.

        Returns (optimal_split_percent, optimal_after_tax_value)
        """
        best_split = 0
        best_value = 0

        # Test splits from 0% to 100% Traditional in 5% increments
        for split in range(0, 101, 5):
            take_home = take_home_at_split(split)
            result = self.calculate_split_projection(
                current_age=current_age,
                retirement_age=retirement_age,
                annual_contribution=annual_contribution,
                employer_match=employer_match,
                retirement_tax_rate=retirement_tax_rate,
                take_home=take_home,
                initial_401k_balance=initial_401k_balance,
                initial_taxable_balance=initial_taxable_balance,
                mega_backdoor_contribution=mega_backdoor_contribution,
                traditional_split=split,
            )
            if result.after_tax_total > best_value:
                best_value = result.after_tax_total
                best_split = split

        return best_split, best_value
