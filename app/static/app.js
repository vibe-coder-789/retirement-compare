let growthChart = null;

document.getElementById('contributionMode').addEventListener('change', function() {
    const label = document.getElementById('contributionLabel');
    if (this.value === 'percentage') {
        label.textContent = 'Contribution (%)';
        document.getElementById('contributionAmount').value = '10';
    } else {
        label.textContent = 'Contribution ($)';
        document.getElementById('contributionAmount').value = '10000';
    }
});

// Update split label when slider changes
document.getElementById('traditionalSplit').addEventListener('input', function() {
    const value = parseInt(this.value);
    const label = document.getElementById('splitLabel');
    if (value === 100) {
        label.textContent = '100% Traditional';
        label.className = 'font-bold text-blue-600';
    } else if (value === 0) {
        label.textContent = '100% Roth';
        label.className = 'font-bold text-green-600';
    } else {
        label.textContent = `${value}% Trad / ${100 - value}% Roth`;
        label.className = 'font-bold text-purple-600';
    }
});

document.getElementById('comparisonForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        current_age: parseInt(document.getElementById('currentAge').value),
        retirement_age: parseInt(document.getElementById('retirementAge').value),
        annual_income: parseFloat(document.getElementById('annualIncome').value),
        annual_bonus: parseFloat(document.getElementById('annualBonus').value) || 0,
        initial_401k_balance: parseFloat(document.getElementById('initial401k').value) || 0,
        initial_taxable_balance: parseFloat(document.getElementById('initialTaxable').value) || 0,
        contribution_mode: document.getElementById('contributionMode').value,
        contribution_amount: parseFloat(document.getElementById('contributionAmount').value),
        contribution_timing: document.getElementById('contributionTiming').value,
        mega_backdoor_contribution: parseFloat(document.getElementById('megaBackdoor').value) || 0,
        traditional_split: parseFloat(document.getElementById('traditionalSplit').value),
        employer_match_percent: parseFloat(document.getElementById('employerMatch').value),
        employer_match_cap_percent: parseFloat(document.getElementById('matchCap').value),
        expected_retirement_income: parseFloat(document.getElementById('retirementIncome').value),
        expected_return: parseFloat(document.getElementById('expectedReturn').value),
        taxable_return: parseFloat(document.getElementById('taxableReturn').value) || 6,
        filing_status: document.getElementById('filingStatus').value,
        savings_rate: parseFloat(document.getElementById('savingsRate').value) || 20,
        current_state: document.getElementById('currentState').value,
        retirement_state: document.getElementById('retirementState').value
    };

    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Calculation failed');
        }

        const result = await response.json();
        displayResults(result);
    } catch (error) {
        document.getElementById('results').innerHTML = `
            <div class="bg-red-100 text-red-700 p-4 rounded-md">
                Error: ${error.message}
            </div>
        `;
    }
});

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatPercent(value) {
    return (value * 100).toFixed(1) + '%';
}

function displayResults(result) {
    const { contribution, tax_comparison, projection_summary } = result;
    const isRothWinner = projection_summary.advantage === 'Roth 401(k)';
    const currentSplit = projection_summary.current_split;
    const optimalSplit = projection_summary.optimal_split;
    const optimalAfterTax = projection_summary.optimal_after_tax;

    // Format split display
    const formatSplit = (split) => {
        if (split === 100) return '100% Traditional';
        if (split === 0) return '100% Roth';
        return `${split}% Trad / ${100 - split}% Roth`;
    };

    document.getElementById('results').innerHTML = `
        <div class="text-center mb-6">
            <span class="winner-badge ${isRothWinner ? 'winner-roth' : 'winner-traditional'}">
                ${projection_summary.advantage} Wins!
            </span>
            <p class="text-gray-600 mt-2">
                By ${formatCurrency(projection_summary.advantage_amount)} after taxes
            </p>
        </div>

        <div class="bg-purple-50 border-l-4 border-purple-500 p-4 mb-4">
            <p class="text-sm text-purple-800">
                <strong>Optimal Split:</strong> ${formatSplit(optimalSplit)}
            </p>
            <p class="text-lg font-bold text-purple-900">
                ${formatCurrency(optimalAfterTax)} after taxes
            </p>
            ${currentSplit !== optimalSplit ? `
                <p class="text-xs text-purple-700 mt-1">
                    Your split (${formatSplit(currentSplit)}) differs from optimal.
                    <button onclick="document.getElementById('traditionalSplit').value=${optimalSplit}; document.getElementById('traditionalSplit').dispatchEvent(new Event('input')); document.getElementById('comparisonForm').dispatchEvent(new Event('submit'));"
                            class="underline font-medium">Apply optimal</button>
                </p>
            ` : `<p class="text-xs text-purple-700 mt-1">You're using the optimal split!</p>`}
            <p class="text-xs text-purple-600 mt-2 italic">
                ${projection_summary.bracket_explanation}
            </p>
        </div>

        <div class="result-card traditional-card">
            <h3 class="font-semibold text-blue-800">100% Traditional Path</h3>
            <p class="text-2xl font-bold text-blue-900">${formatCurrency(projection_summary.traditional_after_tax)}</p>
            <p class="text-sm text-blue-700">After-tax wealth at retirement</p>
        </div>

        <div class="result-card roth-card">
            <h3 class="font-semibold text-green-800">100% Roth Path</h3>
            <p class="text-2xl font-bold text-green-900">${formatCurrency(projection_summary.roth_after_tax)}</p>
            <p class="text-sm text-green-700">After-tax wealth at retirement</p>
        </div>

        <div class="bg-gray-100 p-4 rounded-lg mt-4">
            <h4 class="font-semibold text-gray-700 mb-2">Your Split (${formatSplit(currentSplit)})</h4>
            <p class="text-lg font-bold text-gray-800">${formatCurrency(projection_summary.current_split_after_tax)} after taxes</p>
            <p class="text-xs text-gray-600 mt-1">
                Traditional 401(k): ${formatCurrency(projection_summary.traditional_final_balance)} |
                Roth 401(k): ${formatCurrency(projection_summary.roth_final_balance)} |
                Taxable: ${formatCurrency(projection_summary.traditional_taxable_balance)}
                ${projection_summary.traditional_mega_backdoor_balance > 0 ? `| Mega Backdoor: ${formatCurrency(projection_summary.traditional_mega_backdoor_balance)}` : ''}
            </p>
        </div>

        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mt-4">
            <p class="text-sm text-yellow-800">
                <strong>Annual Tax Savings (if 100% Traditional):</strong>
                ${formatCurrency(tax_comparison.current_year_tax_savings)}
            </p>
            <p class="text-xs text-yellow-700 mt-1">
                Higher take-home → more invested in taxable account
            </p>
        </div>
    `;

    document.getElementById('contributionDetails').innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Your Contribution</span>
            <span class="detail-value">${formatCurrency(contribution.employee_contribution)}/year</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Employer Match</span>
            <span class="detail-value">${formatCurrency(contribution.employer_match)}/year</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Total Annual</span>
            <span class="detail-value">${formatCurrency(contribution.total_contribution)}/year</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">2024 Limit</span>
            <span class="detail-value">${formatCurrency(contribution.max_employee_allowed)}</span>
        </div>
        ${contribution.is_over_limit ? '<p class="text-red-600 text-xs mt-2">Note: Contribution was capped at the annual limit</p>' : ''}
    `;

    const trad = tax_comparison.current_traditional;
    const roth = tax_comparison.current_roth;
    document.getElementById('taxDetails').innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Federal Tax (Trad)</span>
            <span class="detail-value">${formatCurrency(trad.federal_tax)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">State Tax (Trad)</span>
            <span class="detail-value">${formatCurrency(trad.state_tax)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">FICA Tax</span>
            <span class="detail-value">${formatCurrency(trad.fica_tax)}</span>
        </div>
        <div class="detail-row font-semibold">
            <span class="detail-label">Total Tax (Trad)</span>
            <span class="detail-value">${formatCurrency(trad.total_tax)}</span>
        </div>
        <div class="detail-row font-semibold">
            <span class="detail-label">Total Tax (Roth)</span>
            <span class="detail-value">${formatCurrency(roth.total_tax)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Annual Savings</span>
            <span class="detail-value text-green-600">${formatCurrency(tax_comparison.current_year_tax_savings)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Retirement Eff. Rate</span>
            <span class="detail-value">${formatPercent(tax_comparison.retirement_tax_rate)}</span>
        </div>
    `;

    document.getElementById('projectionDetails').innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Total Contributions</span>
            <span class="detail-value">${formatCurrency(projection_summary.total_contributions)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Total Employer Match</span>
            <span class="detail-value">${formatCurrency(projection_summary.total_employer_match)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Growth (Trad)</span>
            <span class="detail-value">${formatCurrency(projection_summary.total_growth_traditional)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Growth (Roth)</span>
            <span class="detail-value">${formatCurrency(projection_summary.total_growth_roth)}</span>
        </div>
    `;

    document.getElementById('chartsSection').style.display = 'block';
    document.getElementById('detailsSection').style.display = 'grid';

    renderChart(result.traditional_projections, result.roth_projections);
}

function renderChart(traditional, roth) {
    const ctx = document.getElementById('growthChart').getContext('2d');

    if (growthChart) {
        growthChart.destroy();
    }

    const labels = traditional.map(p => `Age ${p.age}`);
    const tradData = traditional.map(p => p.after_tax_wealth);
    const rothData = roth.map(p => p.after_tax_wealth);

    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '100% Traditional (After-Tax)',
                    data: tradData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: '100% Roth (After-Tax)',
                    data: rothData,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}
