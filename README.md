# 401(k) Traditional vs Roth Comparison Tool

A web-based calculator that helps you decide the optimal split between Traditional and Roth 401(k) contributions based on your tax situation.

## Features

- **Traditional vs Roth Comparison**: See side-by-side after-tax wealth projections for 100% Traditional vs 100% Roth paths
- **Optimal Split Finder**: Automatically calculates the best Traditional/Roth split to maximize after-tax retirement wealth
- **Tax-Aware Projections**: Accounts for federal tax brackets, state taxes, and FICA taxes
- **State Tax Support**: All 50 US states + DC with pre-configured tax rates
- **Mega Backdoor Roth**: Model additional after-tax contributions converted to Roth
- **Employer Match**: Configure match percentage and cap
- **Taxable Account Modeling**: Tax savings from Traditional contributions are invested in a taxable brokerage account
- **Interactive Charts**: Visualize wealth growth over time with Chart.js

## How It Works

The tool compares two scenarios:

1. **Traditional 401(k)**: Pre-tax contributions reduce your taxable income now. You pay taxes on withdrawals in retirement.

2. **Roth 401(k)**: After-tax contributions (no tax break now). Withdrawals in retirement are tax-free.

The key insight: Traditional contributions generate tax savings today. Those savings, when invested in a taxable account, can grow alongside your 401(k). The tool models this to give you a true apples-to-apples comparison.

## Tax Calculations

- **Federal Income Tax**: 2024 tax brackets for Single and Married Filing Jointly
- **State Income Tax**: Configurable by state (0% for TX, FL, WA, etc. up to 9.9% for OR)
- **FICA Taxes**:
  - Social Security: 6.2% up to $168,600 wage base
  - Medicare: 1.45% on all wages
  - Additional Medicare: 0.9% on wages over $200k (single) / $250k (MFJ)

## Installation

```bash
# Clone the repository
git clone https://github.com/vibe-coder-789/retirement-compare.git
cd retirement-compare

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

## Usage

1. Enter your current age and target retirement age
2. Input your annual salary and bonus
3. Set your 401(k) contribution amount (% or $)
4. Configure employer match (e.g., 50% match up to 6% of salary)
5. Adjust the Traditional/Roth split slider
6. Select your current and retirement states
7. Click "Calculate Comparison"

The tool will show:
- Which strategy wins (Traditional or Roth) and by how much
- The optimal split percentage
- Year-by-year wealth projections
- Tax breakdown (federal, state, FICA)

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Charts**: Chart.js
- **Validation**: Pydantic

## API Endpoints

```
POST /api/compare - Calculate comparison with all projections
GET /api/limits/{year} - Get contribution limits for a given year
```

## Limitations

- Uses simplified flat state tax rates (not progressive brackets)
- Assumes constant income and returns over time
- Does not account for Required Minimum Distributions (RMDs)
- Does not model Social Security benefits
- Capital gains tax uses simplified 15% rate

## License

MIT
